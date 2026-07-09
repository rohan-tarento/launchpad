"""status — programme readiness checklist + kit health.

Two views depending on flag:

  --meta   (PM / Operator view)
    Kit version check (installed vs latest on drivestream-lab)
    Meta repo phase checklist: governance, clone, scaffold, harness
    Constitution pins declared across all harness profiles
    Skills pins declared across all harness profiles
    Foundation freshness: new tags available on scaffold template repos

  --repo <name>   (Engineer / Repo-owner view)
    Kit version check
    Repo phase checklist: governance, clone, scaffold, harness
    Constitution: declared ref vs locally pinned ref (drift check)
    Skills: declared ref vs locally pinned ref (drift check)
    Exit code 1 if drift detected — safe for CI pipelines

check-harness is removed — status --repo covers its functionality.

Usage:
  launchpad status --meta
  launchpad status --repo <name>
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx

from launchpad import __version__
from launchpad.schema import SchemaError

_KIT_REPO = "drivestream-lab/launchpad"
_API_TIMEOUT = 4.0


# ── Helpers ──────────────────────────────────────────────────────────────────


def _find_config(config_dir: Path, pattern: str) -> Path | None:
    matches = list(config_dir.glob(pattern))
    return matches[0] if matches else None


def _mark(ok: bool | None, *, neutral: bool = False) -> str:
    """
    ok=True   → [✔]  done / healthy
    ok=False  → [✗]  expected but missing (action required)
    ok=None   → [?]  unknown / prereq not met
    neutral   → [–]  intentionally off (no action needed)
    """
    if neutral:
        return "–"
    if ok is None:
        return "?"
    return "✔" if ok else "✗"


def _section(title: str) -> None:
    print(f"\n── {title} {'─' * max(0, 54 - len(title))}")


# ── Kit version ──────────────────────────────────────────────────────────────


def _fetch_latest_kit_version() -> str | None:
    """Return latest release tag from drivestream-lab/launchpad, or None on failure."""
    try:
        r = httpx.get(
            f"https://api.github.com/repos/{_KIT_REPO}/releases/latest",
            timeout=_API_TIMEOUT,
            headers={"Accept": "application/vnd.github+json"},
        )
        if r.status_code == 200:
            return r.json().get("tag_name", "").lstrip("v") or None
        # Fall back to tags if no release published
        r2 = httpx.get(
            f"https://api.github.com/repos/{_KIT_REPO}/tags",
            timeout=_API_TIMEOUT,
            headers={"Accept": "application/vnd.github+json"},
        )
        if r2.status_code == 200:
            tags = r2.json()
            if tags:
                return tags[0]["name"].lstrip("v")
    except Exception:
        pass
    return None


def _semver(v: str) -> tuple[int, ...]:
    """Parse a loose semver string like '0.5.10' into a comparable tuple."""
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def _print_kit_section() -> bool:
    """Print kit version block. Returns True if upgrade needed."""
    _section("Kit")
    installed = __version__
    latest = _fetch_latest_kit_version()
    if latest is None:
        print(f"  [?] launchpad v{installed}  (version check unavailable — offline?)")
        return False
    if _semver(latest) <= _semver(installed):
        print(f"  [✔] launchpad v{installed}  (up to date)")
        return False
    print(f"  [!] launchpad v{installed} installed — v{latest} available")
    print(f'      Upgrade: pipx install "launchpad @ git+https://github.com/{_KIT_REPO}@v{latest}"')
    return True


# ── Foundation freshness (PM view) ───────────────────────────────────────────


def _latest_tag(org: str, repo: str) -> str | None:
    try:
        r = httpx.get(
            f"https://api.github.com/repos/{org}/{repo}/tags",
            timeout=_API_TIMEOUT,
            headers={"Accept": "application/vnd.github+json"},
        )
        if r.status_code == 200:
            tags = r.json()
            if tags:
                return tags[0]["name"].lstrip("v")
    except Exception:
        pass
    return None


def _print_foundation_section(sca: Any) -> None:
    """Print foundation freshness for all scaffold entries that have template + ref set."""
    entries: list[tuple[str, str, str]] = []  # (label, org/repo, declared_ref)

    def _collect(label: str, entry: Any) -> None:
        if entry is None:
            return
        t = getattr(entry, "template", "") or ""
        ref = getattr(entry, "ref", "") or ""
        if not t or not ref:
            return
        if t.startswith("gh:"):
            slug = t[3:]  # e.g. drivestream-lab/python-fastapi-foundation
            parts = slug.split("/", 1)
            if len(parts) == 2:
                entries.append((label, slug, ref.lstrip("v")))

    _collect("meta", sca.meta)
    for rname, rentry in (sca.repos or {}).items():
        _collect(rname, rentry)

    if not entries:
        return

    _section("Foundation updates")
    api_unavailable = False
    for label, slug, declared_ref in entries:
        parts = slug.split("/", 1)
        org_slug, repo_slug = parts[0], parts[1]
        latest = _latest_tag(org_slug, repo_slug)
        if latest is None:
            api_unavailable = True
            print(f"  [?] {repo_slug:<38}  v{declared_ref}  (check unavailable)")
        elif latest == declared_ref:
            print(f"  [✔] {repo_slug:<38}  v{declared_ref}  (up to date)")
        else:
            print(f"  [!] {repo_slug:<38}  v{declared_ref} declared — v{latest} available")

    if api_unavailable:
        print("  (some checks skipped — offline?)")


# ── Governance pins (PM view) ─────────────────────────────────────────────────


def _print_governance_pins(h: Any) -> None:
    _section("Governance pins  (declared in harness YAML)")
    for pname, profile in h.profiles.items():
        if profile.constitution is None:
            print(f"  –   {pname:<20}  no constitution (by design)")
        else:
            con = profile.constitution
            print(f"  [→] {pname:<20}  {con.repo:<34}  @ {con.ref}")
        if not profile.skills:
            print(f"  –   {pname:<20}  no skills (by design)")
        else:
            for skill in profile.skills:
                label = f"{skill.org}/{skill.repo}"
                print(f"  [→] {pname:<20}  {label:<34}  @ {skill.ref or 'HEAD'}")


# ── Submodule drift (Engineer view) ───────────────────────────────────────────


def _get_local_submodule_ref(repo_path: Path, submodule_rel: str) -> str | None:
    """Return the current HEAD ref of a submodule, or None if not present."""
    sub_path = repo_path / submodule_rel
    if not sub_path.is_dir():
        return None
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=sub_path,
        capture_output=True,
        text=True,
    )
    sha = result.stdout.strip()
    # Try to resolve the SHA to a tag name
    tag_result = subprocess.run(
        ["git", "describe", "--tags", "--exact-match", sha],
        cwd=sub_path,
        capture_output=True,
        text=True,
    )
    if tag_result.returncode == 0:
        return tag_result.stdout.strip()
    return sha[:7] if sha else None


def _print_submodule_drift(
    *,
    section: str,
    repo_label: str,
    declared_ref: str,
    submodule_rel: str,
    repo_path: Path,
) -> bool:
    """Print declared vs local submodule state. Returns True if drift detected."""
    _section(section)
    print(f"  [→] declared:  {repo_label} @ {declared_ref}")

    local_ref = _get_local_submodule_ref(repo_path, submodule_rel)
    if local_ref is None:
        print("  [✗] local:     not pinned yet")
        return True

    if local_ref == declared_ref:
        print(f"  [✔] local:     {repo_label} @ {local_ref}  (in sync)")
        return False

    print(f"  [!] local:     {repo_label} @ {local_ref}  ← behind declared {declared_ref}")
    return True


def _print_constitution_drift(profile: Any, repo_path: Path) -> bool:
    """Print declared vs local constitution state. Returns True if drift detected."""
    con = profile.constitution
    if con is None:
        _section("Constitution")
        print("  –   no constitution for this profile (by design)")
        return False

    return _print_submodule_drift(
        section="Constitution",
        repo_label=con.repo,
        declared_ref=con.ref,
        submodule_rel=".cursor/rules",
        repo_path=repo_path,
    )


def _print_skills_drift(profile: Any, repo_path: Path) -> bool:
    """Print declared vs local skills submodule state. Returns True if any drift."""
    if not profile.skills:
        _section("Skills")
        print("  –   no skills for this profile (by design)")
        return False

    drift = False
    for skill in profile.skills:
        declared = skill.ref or "HEAD"
        label = f"{skill.org}/{skill.repo}"
        rel = f".agents/skills/{skill.repo}"
        if _print_submodule_drift(
            section=f"Skills  ({skill.repo})",
            repo_label=label,
            declared_ref=declared,
            submodule_rel=rel,
            repo_path=repo_path,
        ):
            drift = True
    return drift


# ── Main ─────────────────────────────────────────────────────────────────────


def run_status(
    *,
    meta: bool = False,
    repo_name: str = "",
    config_dir: Path | None = None,  # None only in tests — main() always resolves via clients.yaml
    workspace: Path | None = None,
) -> int:
    if not meta and not repo_name:
        print("ERROR: pass --meta or --repo <name>", file=sys.stderr)
        return 1

    if config_dir is None:
        # Should not reach here — main() blocks client-less commands early.
        raise RuntimeError("config_dir not resolved — pass --client <id> or run launchpad onboard interview")
    cdir = config_dir

    # Load schemas (best-effort)
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
    meta_repo = prog.meta_repo if prog else (
        cdir.parent.name if cdir.parent.name.endswith("-meta") else "unknown-meta"
    )
    org = prog.org if prog else "unknown"

    if meta:
        target = meta_repo
        stack = (gov.repos[target].stack if gov and target in gov.repos else "meta-pm")
    else:
        target = repo_name
        stack = gov.repos[repo_name].stack if gov and repo_name in gov.repos else ""

    print(f"\nstatus  →  {org}/{target}")

    # ── Kit version ──────────────────────────────────────────────────────────
    kit_upgrade_needed = _print_kit_section()

    # ── Repo phase checklist ─────────────────────────────────────────────────
    _section("Repo")

    gov_ok = gov is not None and target in gov.repos
    stack_label = f"stack: {stack}" if gov_ok and stack else f"add '{target}' to governance repos:"
    print(f"  [{_mark(gov_ok)}] Governance declared       ({stack_label})")

    repo_path = Path(ws).expanduser().resolve() / target
    clone_ok = (repo_path / ".git").is_dir()
    clone_detail = str(repo_path) if clone_ok else (
        f"not a git repo: {repo_path}  (run init-client --apply)"
        if repo_path.is_dir() else f"not found: {repo_path}"
    )
    print(f"  [{_mark(clone_ok)}] Local clone (git repo)    ({clone_detail})")

    # Scaffold — [✔] applied, [–] off (intentional), [✗] enabled but not run
    sca_applied = False
    sca_pending = False
    if meta:
        sca_configured = sca is not None and sca.meta is not None
        sca_enabled = sca_configured and sca.meta.enabled  # type: ignore[union-attr]
    else:
        sca_configured = sca is not None and repo_name in sca.repos
        sca_enabled = sca_configured and sca.repos[repo_name].enabled  # type: ignore[index]

    if not sca_configured or not sca_enabled:
        # Scaffold is intentionally off — neutral, not a failure
        print(f"  [{_mark(None, neutral=True)}] Scaffold                  (off — enable in scaffold YAML to opt in)")
    else:
        # Scaffold is enabled — check marker written by apply-scaffold
        sca_applied = clone_ok and (repo_path / ".launchpad-scaffold").is_file()
        sca_pending = clone_ok and not sca_applied
        print(f"  [{_mark(sca_applied)}] Scaffold                  "
              f"({'applied' if sca_applied else 'enabled but not applied — run apply-scaffold --apply --force'})")

    # Harness — [✔] pinned, [–] no profile (opt-out), [✗] profile defined but not applied, [?] prereq missing
    harness_ok = False
    harness_neutral = False
    harness_detail = ""
    profile = None
    if not clone_ok:
        harness_detail = "clone required first"
    elif not h:
        harness_neutral = True
        harness_detail = "no harness config found"
    else:
        profile_name = h.resolve_profile(target, stack)
        if not profile_name or profile_name not in h.profiles:
            harness_neutral = True
            harness_detail = f"no profile defined for stack '{stack}' — add one to harness YAML to opt in"
        else:
            profile = h.profiles[profile_name]
            con = profile.constitution
            if con is None:
                # Meta/config repos: no constitution needed — harness = CODEOWNERS + harness-pin only
                harness_pin_path = repo_path / ".harness-pin.yaml"
                harness_ok = harness_pin_path.is_file()
                harness_detail = (
                    f"profile: {profile_name}"
                    if harness_ok
                    else f"not applied  (profile: {profile_name}) — run apply-harness --apply"
                )
            else:
                rules_path = repo_path / ".cursor" / "rules"
                harness_ok = rules_path.is_dir()
                for skill in profile.skills:
                    skill_path = repo_path / ".agents" / "skills" / skill.repo
                    if not skill_path.is_dir():
                        harness_ok = False
                        break
                harness_detail = (
                    f"profile: {profile_name}"
                    if harness_ok
                    else f"not applied  (profile: {profile_name}) — run apply-harness --apply"
                )

    if not clone_ok:
        print(f"  [{_mark(None)}] Harness                   ({harness_detail})")
    elif harness_neutral:
        print(f"  [{_mark(None, neutral=True)}] Harness                   ({harness_detail})")
    else:
        print(f"  [{_mark(harness_ok)}] Harness                   ({harness_detail})")

    # ── PM view: constitution pins + foundation freshness ────────────────────
    drift_detected = False
    if meta:
        if h:
            _print_governance_pins(h)
        if sca:
            _print_foundation_section(sca)

    # ── Engineer view: constitution + skills drift ────────────────────────────
    else:
        if profile and clone_ok:
            drift_detected = _print_constitution_drift(profile, repo_path)
            if _print_skills_drift(profile, repo_path):
                drift_detected = True
            if drift_detected:
                client = os.environ.get("LAUNCHPAD_CLIENT", "").strip()
                prefix = f"--client {client} " if client else ""
                print(f"      Fix: launchpad {prefix}apply-harness --repo {target} --apply")

    # ── NEXT ─────────────────────────────────────────────────────────────────
    print()
    client_id = os.environ.get("LAUNCHPAD_CLIENT", "").strip()
    client_prefix = f"--client {client_id} " if client_id else ""
    flag = "--meta" if meta else f"--repo {target}"
    if kit_upgrade_needed:
        next_cmd = "upgrade launchpad kit (see Kit section above)"
    elif not gov_ok:
        next_cmd = f"add '{target}' to governance-{org}.yaml repos"
    elif not clone_ok:
        next_cmd = f"launchpad {client_prefix}init-client {flag} --apply"
    elif sca_pending:
        next_cmd = f"launchpad {client_prefix}apply-scaffold {flag} --apply --force"
    elif not harness_neutral and not harness_ok and clone_ok:
        next_cmd = f"launchpad {client_prefix}apply-harness {flag} --apply"
    elif drift_detected:
        next_cmd = f"launchpad {client_prefix}apply-harness --repo {target} --apply"
    else:
        next_cmd = f"launchpad {client_prefix}status {flag}  (all checks pass)"

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  NEXT:                                                       ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  {next_cmd:<60}  ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # Exit 1 for actionable failures — neutral states (scaffold off, no profile) are not failures
    has_failure = (
        not gov_ok
        or not clone_ok
        or sca_pending
        or (not harness_neutral and not harness_ok and clone_ok)
        or drift_detected
    )
    return 1 if has_failure else 0
