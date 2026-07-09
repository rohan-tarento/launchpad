"""apply-harness — pin constitution + skills submodules per stack.

Reads harness-<org>.yaml + governance-<org>.yaml.
harness_profile resolves as: repos.<name> override → repo.stack from governance.

Usage:
  launchpad apply-harness --meta [--apply]
  launchpad apply-harness --repo <name> [--apply]
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from launchpad.schema import SchemaError
from launchpad.schema.harness import HarnessProfile, SkillRef, load_harness
from launchpad.schema.governance import load_governance

# Sentinel placeholder used in kit CODEOWNERS templates.
# All templates ship with this string; apply-harness substitutes the real org.
_TEMPLATE_ORG_PLACEHOLDER = "example-org"

# Default prayog dev skills seeded into harness-pin when template is rendered.
_DEFAULT_DEV_SKILLS = [
    "spec-draft",
    "initiative-feasibility",
    "spec-technical-review",
    "spec-implementation-plan",
    "pre-implement",
    "loop-spec",
    "ground-spec",
    "verify",
]


def _run_git(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _pin_git_ref(repo_dir: Path, ref: str, *, label: str = "") -> bool:
    """Fetch and force-checkout a tag or branch inside a git repo."""
    if not repo_dir.is_dir():
        return False

    prefix = f"  {label}: " if label else "  "
    print(f"{prefix}fetching {ref!r} …")

    # Tags need an explicit refspec — `git fetch origin v0.1.5` only updates FETCH_HEAD.
    fetch = _run_git(
        ["git", "fetch", "origin", f"refs/tags/{ref}:refs/tags/{ref}"],
        cwd=repo_dir,
    )
    if fetch.returncode != 0:
        fetch = _run_git(["git", "fetch", "origin", ref], cwd=repo_dir)
    if fetch.returncode != 0:
        print(f"  WARN: fetch {ref!r} failed: {fetch.stderr.strip()}", file=sys.stderr)
        return False

    print(f"{prefix}checkout {ref!r} …")
    checkout = _run_git(["git", "checkout", "-f", ref], cwd=repo_dir)
    if checkout.returncode != 0:
        print(f"  WARN: checkout {ref!r} failed: {checkout.stderr.strip()}", file=sys.stderr)
        return False
    return True


def _pin_submodule(
    repo_path: Path,
    submodule_rel: str,
    url: str,
    ref: str,
    *,
    label: str = "",
) -> bool:
    """Ensure submodule exists at repo_path/submodule_rel and pin it to ref."""
    if not (repo_path / ".git").is_dir():
        print(f"  WARN: {repo_path} is not a git repo — cannot pin submodule", file=sys.stderr)
        return False

    tag = label or submodule_rel
    submodule_dest = repo_path / submodule_rel
    gitmodules = repo_path / ".gitmodules"
    already_added = gitmodules.is_file() and url in gitmodules.read_text()

    if not already_added:
        print(f"  {tag}: adding submodule {url} → {submodule_rel} …")
        result = _run_git(
            ["git", "submodule", "add", "--force", url, submodule_rel],
            cwd=repo_path,
        )
        if result.returncode != 0:
            print(f"  WARN: submodule add failed: {result.stderr.strip()}", file=sys.stderr)
            return False
    else:
        print(f"  {tag}: submodule exists — pinning {ref!r} …")

    if not _pin_git_ref(submodule_dest, ref, label=tag):
        return False

    _run_git(["git", "add", submodule_rel], cwd=repo_path)
    return True


def _find_config(config_dir: Path, pattern: str) -> Path | None:
    matches = list(config_dir.glob(pattern))
    return matches[0] if matches else None


def _kit_templates_dir() -> Path:
    """Resolve the kit's templates/ directory (inside the launchpad package).

    Works identically whether installed from local source or from a git tag:
      __file__ = .../site-packages/launchpad/commands/apply_harness.py
      .parent  = .../site-packages/launchpad/commands/
      .parent  = .../site-packages/launchpad/
      / "templates" = .../site-packages/launchpad/templates/
    """
    return Path(__file__).resolve().parent.parent / "templates"


def _resolve_kit_template(filename: str) -> Path | None:
    """Return path to a template file, or None if not found."""
    path = _kit_templates_dir() / filename
    return path if path.is_file() else None


def _seed_codeowners(repo_path: Path, tpl_name: str, org: str, *, apply: bool) -> None:
    """Write .github/CODEOWNERS from the template file declared in harness-<org>.yaml."""
    tpl_path = _resolve_kit_template(tpl_name)

    if tpl_path is None:
        print(f"  WARN: CODEOWNERS template '{tpl_name}' not found in kit templates/ — skipping")
        print(f"        Set codeowners_template: <filename> in harness-<org>.yaml profiles")
        return

    dest = repo_path / ".github" / "CODEOWNERS"

    if not apply:
        print(f"    [dry-run] CODEOWNERS  ← {tpl_name}  →  .github/CODEOWNERS")
        print(f"              (replace '{_TEMPLATE_ORG_PLACEHOLDER}' → '{org}')")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    content = tpl_path.read_text(encoding="utf-8").replace(_TEMPLATE_ORG_PLACEHOLDER, org)
    dest.write_text(content, encoding="utf-8")
    print(f"  ✔  CODEOWNERS  ← {tpl_name}  (org: {org})")


def _seed_harness_pin(
    repo_path: Path,
    tpl_name: str,
    profile: HarnessProfile,
    profile_name: str,
    *,
    apply: bool,
) -> None:
    """Write or sync .harness-pin.yaml from the kit template + harness profile refs."""
    tpl_path = _resolve_kit_template(tpl_name)

    if tpl_path is None:
        print(f"  WARN: harness-pin template '{tpl_name}' not found in kit templates/ — skipping")
        print(f"        Set harness_pin_template: <filename> in harness-<org>.yaml profiles")
        return

    dest = repo_path / ".harness-pin.yaml"
    con = profile.constitution
    skill = profile.skills[0] if profile.skills else None
    skills_block = "\n".join(f"    - {name}" for name in _DEFAULT_DEV_SKILLS)

    if not apply:
        print(f"    [dry-run] harness-pin ← {tpl_name}  →  .harness-pin.yaml")
        return

    content = tpl_path.read_text(encoding="utf-8")
    if con:
        content = content.replace("{{RULES_REF}}", con.ref)
        content = content.replace(
            "repo: drivestream-lab/python-services-rules",
            f"repo: {con.org}/{con.repo}",
        )
        content = content.replace(
            "repo: drivestream-lab/nextjs-bff-rules",
            f"repo: {con.org}/{con.repo}",
        )
    if skill:
        content = content.replace("{{AGENT_SKILLS_REF}}", skill.ref or "HEAD")
        content = content.replace(
            "repo: drivestream-lab/prayog-skills",
            f"repo: {skill.org}/{skill.repo}",
        )
    content = content.replace("{{AGENT_SKILLS_LIST}}", skills_block)

    dest.write_text(content, encoding="utf-8")
    print(f"  ✔  harness-pin synced ← {tpl_name}  (profile: {profile_name})")


def _remove_legacy_cursor_skills(repo_path: Path, *, apply: bool) -> None:
    """Remove pre-v0.5.10 `.cursor/skills` submodule if present."""
    legacy_rel = ".cursor/skills"
    legacy = repo_path / ".cursor" / "skills"
    gitmodules = repo_path / ".gitmodules"
    in_gitmodules = gitmodules.is_file() and legacy_rel in gitmodules.read_text()

    if not in_gitmodules and not legacy.is_dir():
        return

    if not apply:
        print(f"    [dry-run] remove legacy {legacy_rel} submodule")
        return

    if in_gitmodules:
        subprocess.run(
            ["git", "submodule", "deinit", "-f", legacy_rel],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "rm", "-rf", legacy_rel],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
    if legacy.is_dir():
        shutil.rmtree(legacy, ignore_errors=True)
    print(f"  ✔  removed legacy {legacy_rel}")


def _apply_harness_to_repo(
    repo_path: Path,
    profile: HarnessProfile,
    profile_name: str,
    org: str,
    *,
    apply: bool = False,
) -> None:
    """Pin constitution submodule, seed agent skills, CODEOWNERS, and harness-pin.

    constitution is optional — profiles without one (e.g. meta-pm) skip the
    submodule step entirely and only seed CODEOWNERS + harness-pin.
    Template filenames come from the profile YAML, not hardcoded Python maps.
    """
    con = profile.constitution  # None when profile has no constitution (e.g. meta-pm)
    submodule_dest = repo_path / ".cursor" / "rules"

    if not apply:
        if con:
            print(f"    [dry-run] constitution submodule: {con.submodule_url}@{con.ref}")
        else:
            print(f"    [dry-run] constitution: (none — no .cursor/rules submodule for this profile)")
        for skill in profile.skills:
            skill_url = f"https://github.com/{skill.org}/{skill.repo}"
            skill_path_rel = f".agents/skills/{skill.repo}"
            print(
                f"    [dry-run] skills submodule: {skill_path_rel} "
                f"← {skill_url}@{skill.ref}"
            )
        _seed_codeowners(repo_path, profile.codeowners_template, org, apply=False)
        _seed_harness_pin(repo_path, profile.harness_pin_template, profile, profile_name, apply=False)
        return

    # Constitution submodule — skip entirely if profile has none
    if con:
        submodule_path_rel = ".cursor/rules"
        submodule_dest.parent.mkdir(parents=True, exist_ok=True)
        if _pin_submodule(
            repo_path,
            submodule_path_rel,
            con.submodule_url,
            con.ref,
            label="constitution",
        ):
            print(f"  ✔  constitution pinned: {con.repo}@{con.ref}")
        else:
            print(f"  ✗  constitution pin failed: {con.submodule_url}@{con.ref}", file=sys.stderr)
    else:
        print(f"  –  constitution: (none — meta/config repo, no rules submodule)")

    # Skills — git submodules under .agents/skills/<repo> (same governance model as constitution)
    _remove_legacy_cursor_skills(repo_path, apply=True)

    for skill in profile.skills:
        skill_url = f"https://github.com/{skill.org}/{skill.repo}"
        skill_path_rel = f".agents/skills/{skill.repo}"
        skill_ref = skill.ref or "HEAD"
        if _pin_submodule(
            repo_path,
            skill_path_rel,
            skill_url,
            skill_ref,
            label=f"skills/{skill.repo}",
        ):
            print(f"  ✔  skills pinned: {skill.org}/{skill.repo}@{skill_ref}")
        else:
            print(
                f"  ✗  skills pin failed: {skill_url}@{skill_ref}",
                file=sys.stderr,
            )

    # CODEOWNERS and harness-pin — filenames come from YAML profile
    _seed_codeowners(repo_path, profile.codeowners_template, org, apply=True)
    _seed_harness_pin(repo_path, profile.harness_pin_template, profile, profile_name, apply=True)


def run_apply_harness(
    *,
    meta: bool = False,
    repo_name: str = "",
    apply: bool = False,
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

    harness_path = _find_config(cdir, "harness-*.yaml")
    if harness_path is None:
        print(f"ERROR: harness-<org>.yaml not found in {cdir}", file=sys.stderr)
        return 1

    gov_path = _find_config(cdir, "governance-*.yaml")
    if gov_path is None:
        print(f"ERROR: governance-<org>.yaml not found in {cdir}", file=sys.stderr)
        return 1

    try:
        h = load_harness(harness_path)
        gov = load_governance(gov_path)
    except SchemaError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    org = gov.org

    try:
        prog_path = cdir / "programme.yaml"
        if prog_path.is_file():
            from launchpad.schema.programme import load_programme
            prog = load_programme(prog_path)
            ws = workspace or prog.workspace
            meta_repo = prog.meta_repo
            slug = prog.programme_slug
        else:
            ws = workspace or Path(".").resolve().parent
            meta_repo = cdir.parent.name
            slug = meta_repo.replace("-meta", "")
    except SchemaError:
        ws = workspace or Path(".").resolve().parent
        meta_repo = cdir.parent.name
        slug = meta_repo.replace("-meta", "")

    if meta:
        target = meta_repo
        # Read stack from governance so tenants can name their meta stack freely.
        stack = gov.repos[target].stack if target in gov.repos else "meta-pm"
    else:
        target = repo_name
        if repo_name not in gov.repos:
            print(f"ERROR: repo '{repo_name}' not in governance yaml", file=sys.stderr)
            return 1
        stack = gov.repos[repo_name].stack

    profile_name = h.resolve_profile(target, stack)
    if profile_name is None or profile_name not in h.profiles:
        print(f"  No harness profile found for {target} (stack={stack}) — skipping.")
        print(f"  Add a '{stack}' profile to harness-{h.org}.yaml and re-run.")
        return 0

    profile = h.profiles[profile_name]
    repo_path = Path(ws).expanduser().resolve() / target

    print(f"apply-harness  →  {h.org}/{target}  [profile: {profile_name}]")
    if not repo_path.is_dir():
        print(f"  WARN: local clone not found at {repo_path}")
        print(f"  Clone it first, then re-run apply-harness.")
        if not apply:
            pass
        else:
            return 1

    _apply_harness_to_repo(repo_path, profile, profile_name, org, apply=apply)

    if not apply:
        print()
        target_flag = "--meta" if meta else f"--repo {target}"
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  NEXT:                                                       ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  launchpad apply-harness {target_flag} --apply{'':<31}  ║")
        print("╚══════════════════════════════════════════════════════════════╝")
    else:
        print()
        import os
        client_id = os.environ.get("LAUNCHPAD_CLIENT", "").strip()
        client_prefix = f"--client {client_id} " if client_id else ""
        target_flag = "--meta" if meta else f"--repo {target}"
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  NEXT:                                                       ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  launchpad {client_prefix}status {target_flag:<41}  ║")
        print("╚══════════════════════════════════════════════════════════════╝")

    return 0
