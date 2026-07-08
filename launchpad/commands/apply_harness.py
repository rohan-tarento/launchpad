"""apply-harness — pin constitution submodule + seed agent skills per stack.

Reads harness-<org>.yaml + governance-<org>.yaml.
harness_profile resolves as: repos.<name> override → repo.stack from governance.

Usage:
  launchpad apply-harness --meta [--apply]
  launchpad apply-harness --repo <name> [--apply]
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from launchpad.schema import SchemaError
from launchpad.schema.harness import HarnessProfile, load_harness
from launchpad.schema.governance import load_governance

def _find_config(config_dir: Path, pattern: str) -> Path | None:
    matches = list(config_dir.glob(pattern))
    return matches[0] if matches else None


def _kit_templates_dir() -> Path:
    """Resolve the kit's templates/ directory (sibling of launchpad package)."""
    return Path(__file__).resolve().parent.parent.parent / "templates"


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
        print(f"              (replace 'example-org' → '{org}')")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    content = tpl_path.read_text(encoding="utf-8").replace("example-org", org)
    dest.write_text(content, encoding="utf-8")
    print(f"  ✔  CODEOWNERS  ← {tpl_name}  (org: {org})")


def _seed_harness_pin(repo_path: Path, tpl_name: str, *, apply: bool) -> None:
    """Write .harness-pin.yaml from the template file declared in harness-<org>.yaml."""
    tpl_path = _resolve_kit_template(tpl_name)

    if tpl_path is None:
        print(f"  WARN: harness-pin template '{tpl_name}' not found in kit templates/ — skipping")
        print(f"        Set harness_pin_template: <filename> in harness-<org>.yaml profiles")
        return

    dest = repo_path / ".harness-pin.yaml"

    if not apply:
        print(f"    [dry-run] harness-pin ← {tpl_name}  →  .harness-pin.yaml")
        return

    if dest.is_file():
        print(f"  SKIP: .harness-pin.yaml already exists (edit manually to upgrade)")
        return

    shutil.copy(tpl_path, dest)
    print(f"  ✔  harness-pin  ← {tpl_name}")


def _apply_harness_to_repo(
    repo_path: Path,
    profile: HarnessProfile,
    org: str,
    *,
    apply: bool = False,
) -> None:
    """Pin constitution submodule, seed agent skills, CODEOWNERS, and harness-pin.

    Template filenames for CODEOWNERS and harness-pin are read from the
    profile (harness-<org>.yaml), not from any hardcoded map in Python.
    """
    con = profile.constitution
    submodule_url = con.submodule_url
    submodule_dest = repo_path / ".cursor" / "rules"

    if not apply:
        print(f"    [dry-run] constitution submodule: {submodule_url}@{con.ref}")
        for skill in profile.skills:
            print(f"    [dry-run] skill: https://github.com/{skill.org}/{skill.repo}@{skill.ref}")
        _seed_codeowners(repo_path, profile.codeowners_template, org, apply=False)
        _seed_harness_pin(repo_path, profile.harness_pin_template, apply=False)
        return

    # Constitution submodule
    import subprocess

    submodule_dest.parent.mkdir(parents=True, exist_ok=True)
    if not (repo_path / ".git").is_dir():
        print(f"  WARN: {repo_path} is not a git repo — cannot add submodule", file=sys.stderr)
        return

    gitmodules = repo_path / ".gitmodules"
    submodule_path_rel = ".cursor/rules"
    already_added = gitmodules.is_file() and submodule_url in gitmodules.read_text()

    if not already_added:
        result = subprocess.run(
            ["git", "submodule", "add", "--force", submodule_url, submodule_path_rel],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  WARN: submodule add failed: {result.stderr.strip()}", file=sys.stderr)

    # Pin to ref
    result = subprocess.run(
        ["git", "-C", str(submodule_dest), "fetch", "origin", con.ref],
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(submodule_dest), "checkout", con.ref],
        capture_output=True,
        text=True,
    )
    print(f"  ✔  constitution: {submodule_url}@{con.ref}")

    # Skills
    for skill in profile.skills:
        skill_url = f"https://github.com/{skill.org}/{skill.repo}"
        skill_path_rel = f".cursor/skills/{skill.repo}"
        skill_dest = repo_path / skill_path_rel
        if not skill_dest.is_dir():
            subprocess.run(
                ["git", "submodule", "add", "--force", skill_url, skill_path_rel],
                cwd=repo_path,
                capture_output=True,
            )
        if skill.ref:
            subprocess.run(["git", "-C", str(skill_dest), "checkout", skill.ref], capture_output=True)
        print(f"  ✔  skill: {skill_url}@{skill.ref or 'HEAD'}")

    # CODEOWNERS and harness-pin — filenames come from YAML profile
    _seed_codeowners(repo_path, profile.codeowners_template, org, apply=True)
    _seed_harness_pin(repo_path, profile.harness_pin_template, apply=True)


def run_apply_harness(
    *,
    meta: bool = False,
    repo_name: str = "",
    apply: bool = False,
    config_dir: Path | None = None,
    workspace: Path | None = None,
) -> int:
    if not meta and not repo_name:
        print("ERROR: pass --meta or --repo <name>", file=sys.stderr)
        return 1

    cdir = config_dir or (Path(".").resolve() / "config")

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
        stack = "meta-pm"
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

    _apply_harness_to_repo(repo_path, profile, org, apply=apply)

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
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  NEXT:                                                       ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        target_flag = "--meta" if meta else f"--repo {target}"
        print(f"║  launchpad check-harness {target_flag:<35}  ║")
        print("╚══════════════════════════════════════════════════════════════╝")

    return 0
