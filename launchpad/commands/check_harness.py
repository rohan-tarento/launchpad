"""check-harness — verify harness pins and submodule state.

Reads harness-<org>.yaml + governance-<org>.yaml.
Reports mismatched refs, missing submodules, and missing AGENTS.md.

Usage:
  launchpad check-harness --meta
  launchpad check-harness --repo <name>
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from launchpad.schema import SchemaError
from launchpad.schema.harness import HarnessProfile, load_harness
from launchpad.schema.governance import load_governance


def _find_config(config_dir: Path, pattern: str) -> Path | None:
    matches = list(config_dir.glob(pattern))
    return matches[0] if matches else None


def _check_submodule(repo_path: Path, submodule_rel: str, expected_ref: str) -> list[str]:
    issues: list[str] = []
    sub_path = repo_path / submodule_rel
    if not sub_path.is_dir():
        issues.append(f"Missing submodule: {submodule_rel}")
        return issues

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=sub_path,
        capture_output=True,
        text=True,
    )
    actual_sha = result.stdout.strip()

    # Resolve expected_ref to SHA
    resolve = subprocess.run(
        ["git", "rev-parse", expected_ref],
        cwd=sub_path,
        capture_output=True,
        text=True,
    )
    expected_sha = resolve.stdout.strip()

    if actual_sha and expected_sha and actual_sha != expected_sha:
        issues.append(
            f"Submodule {submodule_rel} is at {actual_sha[:7]} but harness pins {expected_ref} ({expected_sha[:7]})"
        )
    return issues


def _check_harness_for_repo(
    repo_path: Path,
    profile: HarnessProfile,
) -> list[str]:
    issues: list[str] = []
    if not repo_path.is_dir():
        return [f"Local clone not found: {repo_path}"]

    issues.extend(_check_submodule(repo_path, ".cursor/rules", profile.constitution.ref))

    for skill in profile.skills:
        skill_rel = f".cursor/skills/{skill.repo}"
        skill_path = repo_path / skill_rel
        if not skill_path.is_dir():
            issues.append(f"Missing skill submodule: {skill_rel}")
        elif skill.ref:
            issues.extend(_check_submodule(repo_path, skill_rel, skill.ref))

    agents_md = repo_path / "AGENTS.md"
    if not agents_md.is_file():
        issues.append("AGENTS.md not found (run apply-harness --apply)")

    return issues


def run_check_harness(
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

    harness_path = _find_config(cdir, "harness-*.yaml")
    gov_path = _find_config(cdir, "governance-*.yaml")
    if harness_path is None or gov_path is None:
        print("ERROR: harness or governance YAML not found", file=sys.stderr)
        return 1

    try:
        h = load_harness(harness_path)
        gov = load_governance(gov_path)
    except SchemaError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        prog_path = cdir / "programme.yaml"
        if prog_path.is_file():
            from launchpad.schema.programme import load_programme
            prog = load_programme(prog_path)
            ws = workspace or prog.workspace
            meta_repo = prog.meta_repo
        else:
            ws = workspace or Path(".").resolve().parent
            meta_repo = cdir.parent.name
    except SchemaError:
        ws = workspace or Path(".").resolve().parent
        meta_repo = cdir.parent.name

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
        print(f"  No harness profile for {target} (stack={stack}) — nothing to check.")
        return 0

    profile = h.profiles[profile_name]
    repo_path = Path(ws).expanduser().resolve() / target

    print(f"check-harness  →  {h.org}/{target}  [profile: {profile_name}]")

    issues = _check_harness_for_repo(repo_path, profile)
    if issues:
        for issue in issues:
            print(f"  ✗  {issue}")
        target_flag = "--meta" if meta else f"--repo {target}"
        print()
        print(f"  Fix: launchpad apply-harness {target_flag} --apply")
        return 1

    print(f"  ✔  constitution  {profile.constitution.repo}@{profile.constitution.ref}")
    for skill in profile.skills:
        print(f"  ✔  skill         {skill.repo}@{skill.ref or 'HEAD'}")
    print(f"  ✔  AGENTS.md")
    print()
    print("  check-harness: OK")
    return 0
