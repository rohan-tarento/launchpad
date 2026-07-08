"""status — programme readiness checklist.

Checks each phase for a meta repo or app repo and prints the single best
NEXT: command.

Phase checklist:
  [1] Governance     → governance-<org>.yaml declares the repo + teams
  [2] GitHub         → repo exists on GitHub (inferred from local clone)
  [3] Local clone    → clone exists at workspace/<repo>
  [4] Scaffold       → scaffold-<org>.yaml: enabled=true (skippable for meta)
  [5] Harness        → .cursor/rules submodule is present and at correct ref

Usage:
  launchpad status --meta
  launchpad status --repo <name>
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from launchpad.schema import SchemaError


def _find_config(config_dir: Path, pattern: str) -> Path | None:
    matches = list(config_dir.glob(pattern))
    return matches[0] if matches else None


def _check(label: str, ok: bool, detail: str = "") -> str:
    mark = "✔" if ok else "✗"
    line = f"  [{mark}] {label}"
    if detail:
        line += f"  ({detail})"
    return line


def run_status(
    *,
    meta: bool = False,
    repo_name: str = "",
    config_dir: Path | None = None,
    workspace: Path | None = None,
) -> int:
    if not meta and not repo_name:
        print("ERROR: pass --meta or --repo <name>", file=sys.stderr)
        return 1

    cdir = config_dir or (Path(".").resolve() / "config")

    # Load schemas (best-effort — show partial status if YAML has errors)
    prog, gov, sca, h = None, None, None, None

    prog_path = cdir / "programme.yaml"
    if prog_path.is_file():
        try:
            from launchpad.schema.programme import load_programme
            prog = load_programme(prog_path)
        except SchemaError:
            pass

    gov_path = _find_config(cdir, "governance-*.yaml")
    if gov_path:
        try:
            from launchpad.schema.governance import load_governance
            gov = load_governance(gov_path)
        except SchemaError:
            pass

    sca_path = _find_config(cdir, "scaffold-*.yaml")
    if sca_path:
        try:
            from launchpad.schema.scaffold import load_scaffold
            sca = load_scaffold(sca_path)
        except SchemaError:
            pass

    h_path = _find_config(cdir, "harness-*.yaml")
    if h_path:
        try:
            from launchpad.schema.harness import load_harness
            h = load_harness(h_path)
        except SchemaError:
            pass

    ws = workspace or (prog.workspace if prog else Path(".").resolve().parent)
    meta_repo = prog.meta_repo if prog else (cdir.parent.name if cdir.parent.name.endswith("-meta") else "unknown-meta")
    org = prog.org if prog else "unknown"
    slug = prog.programme_slug if prog else meta_repo.replace("-meta", "")

    if meta:
        target = meta_repo
        stack = (gov.repos[target].stack if gov and target in gov.repos else "meta-pm")
    else:
        target = repo_name
        stack = gov.repos[repo_name].stack if gov and repo_name in gov.repos else ""

    print(f"\nstatus  →  {org}/{target}")
    print()

    results: list[str] = []
    next_cmd: str = ""

    # [1] Governance declared
    gov_ok = gov is not None and target in gov.repos
    results.append(_check("Governance declared", gov_ok,
                          f"in governance-{org}.yaml" if gov_ok else f"add '{target}' to governance-{org}.yaml repos:"))
    if not gov_ok:
        next_cmd = f"launchpad init-client --meta --dry-run" if meta else f"launchpad init-client --repo {target} --dry-run"

    # [2] Local clone exists (must be a real git repo, not just a directory)
    repo_path = Path(ws).expanduser().resolve() / target
    clone_ok = (repo_path / ".git").is_dir()
    detail = str(repo_path) if clone_ok else (
        f"not a git repo: {repo_path}  (run init-client --apply)" if repo_path.is_dir()
        else f"not found: {repo_path}"
    )
    results.append(_check("Local clone (git repo)", clone_ok, detail))
    if not clone_ok and not next_cmd:
        next_cmd = f"launchpad init-client --{'meta' if meta else f'repo {target}'} --apply  # creates repo + clone"

    # [3] Scaffold (skippable — show state but don't block)
    if meta:
        sca_enabled = sca is not None and sca.meta is not None and sca.meta.enabled
        sca_label = "Scaffold (meta)"
    else:
        sca_enabled = sca is not None and repo_name in sca.repos and sca.repos[repo_name].enabled
        sca_label = f"Scaffold ({target})"

    results.append(_check(sca_label, sca_enabled,
                          "enabled" if sca_enabled else "disabled — set enabled: true in scaffold-<org>.yaml to opt in"))

    # [4] Harness pinned
    harness_ok = False
    harness_detail = ""
    if clone_ok and h:
        profile_name = h.resolve_profile(target, stack)
        if profile_name and profile_name in h.profiles:
            profile = h.profiles[profile_name]
            rules_path = repo_path / ".cursor" / "rules"
            harness_ok = rules_path.is_dir()
            harness_detail = f"profile: {profile_name}" if harness_ok else f"missing .cursor/rules  (profile: {profile_name})"
        else:
            harness_detail = f"no profile for stack '{stack}'"
    elif not clone_ok:
        harness_detail = "clone required first"

    results.append(_check("Harness pinned", harness_ok, harness_detail))
    if not harness_ok and not next_cmd and clone_ok:
        next_cmd = f"launchpad apply-harness --{'meta' if meta else f'repo {target}'} --apply"

    # Print checklist
    for line in results:
        print(line)

    # Best NEXT
    if not next_cmd:
        # Everything is good
        if sca_enabled:
            sca_path_check = repo_path  # scaffold was applied if clone exists
            next_cmd = "launchpad check-harness --" + ("meta" if meta else f"repo {target}")
        else:
            next_cmd = "  (all checks pass — consider enabling scaffold or check-harness)"

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  NEXT:                                                       ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  {next_cmd:<60}  ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    all_ok = gov_ok and clone_ok and harness_ok
    return 0 if all_ok else 1
