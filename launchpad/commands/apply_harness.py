"""apply-harness — pin constitution + skills submodules per stack.

Reads harness-<org>.yaml + governance-<org>.yaml.
harness_profile resolves as: repos.<name> override → repo.stack from governance.

Usage:
  launchpad apply-harness --meta [--apply]
  launchpad apply-harness --repo <name> [--apply]
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from launchpad.harness.community_skills import community_skill_names, install_community_skills
from launchpad.harness.paths import (
    HARNESS_PROFILE_REL,
    PM_HARNESS_PROFILE,
    PRAYOG_SKILLS_SUBMODULE_REL,
)
from launchpad.harness.skills_materialize import lane_key_for_profile, materialize_skill_tree
from launchpad.harness.skills_resolve import (
    HarnessResolveError,
    copy_harness_profile,
    resolve_skill_names,
    slash_list,
)
from launchpad.harness.submodules import pin_submodule
from launchpad.schema import SchemaError
from launchpad.schema.harness import HarnessProfile, load_harness
from launchpad.schema.governance import load_governance
from launchpad.ui import print_next_box

_TEMPLATE_ORG_PLACEHOLDER = "example-org"


def _find_config(config_dir: Path, pattern: str) -> Path | None:
    matches = list(config_dir.glob(pattern))
    return matches[0] if matches else None


def _kit_templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "templates"


def _resolve_kit_template(filename: str) -> Path | None:
    path = _kit_templates_dir() / filename
    return path if path.is_file() else None


def _community_skills_yaml_block(profile: HarnessProfile) -> str:
    if not profile.community_skills:
        return "community_skills: []"
    lines = ["community_skills:"]
    for spec in profile.community_skills:
        lines.append(f"  - source: {spec.source}")
        lines.append(f"    ref: {spec.ref}")
        lines.append(f"    skill: {spec.skill}")
    return "\n".join(lines)


def _seed_codeowners(repo_path: Path, tpl_name: str, org: str, *, apply: bool) -> None:
    tpl_path = _resolve_kit_template(tpl_name)
    if tpl_path is None:
        print(f"  WARN: CODEOWNERS template '{tpl_name}' not found in kit templates/ — skipping")
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
    skill_names: list[str],
    *,
    apply: bool,
) -> None:
    tpl_path = _resolve_kit_template(tpl_name)
    if tpl_path is None:
        print(f"  WARN: harness-pin template '{tpl_name}' not found in kit templates/ — skipping")
        return

    if not apply:
        print(f"    [dry-run] harness-pin ← {tpl_name}  →  .harness-pin.yaml")
        return

    dest = repo_path / ".harness-pin.yaml"
    con = profile.constitution
    skill = profile.skills[0] if profile.skills else None
    skills_block = "\n".join(f"    - {name}" for name in skill_names)

    content = tpl_path.read_text(encoding="utf-8")
    if con:
        content = content.replace("{{RULES_REF}}", con.ref)
        for rules_repo in (
            "drivestream-lab/python-services-rules",
            "drivestream-lab/nextjs-bff-rules",
            "drivestream-lab/terraform-infra-rules",
            "drivestream-lab/data-platform-rules",
        ):
            content = content.replace(f"repo: {rules_repo}", f"repo: {con.org}/{con.repo}")

    if skill:
        content = content.replace("{{AGENT_SKILLS_REF}}", skill.ref or "HEAD")
        content = content.replace(
            "repo: drivestream-lab/prayog-skills",
            f"repo: {skill.org}/{skill.repo}",
        )
    content = content.replace("{{AGENT_SKILLS_LIST}}", skills_block)

    community_block = _community_skills_yaml_block(profile)
    if "community_skills:" in content:
        content = re.sub(
            r"community_skills:\n(?:[ \t]+-[^\n]*\n(?:[ \t]+[^\n]*\n)*)*",
            community_block + "\n",
            content,
            count=1,
        )

    dest.write_text(content, encoding="utf-8")
    print(f"  ✔  harness-pin synced ← {tpl_name}  (profile: {profile_name})")


def _seed_agents_md(
    repo_path: Path,
    profile_name: str,
    profile: HarnessProfile,
    skill_names: list[str],
    *,
    target: str,
    org: str,
    meta_repo: str,
    apply: bool,
) -> None:
    is_meta = profile_name == PM_HARNESS_PROFILE
    tpl_name = "AGENTS.meta.md" if is_meta else "AGENTS.md"
    tpl_path = _resolve_kit_template(tpl_name)
    if tpl_path is None:
        return

    if not apply:
        print(f"    [dry-run] AGENTS.md  ← {tpl_name}")
        return

    con = profile.constitution
    skill = profile.skills[0] if profile.skills else None
    content = tpl_path.read_text(encoding="utf-8")
    content = content.replace("{{DISPLAY_NAME}}", org)
    content = content.replace("{{ORG}}", org)
    content = content.replace("{{META_REPO}}", meta_repo)
    content = content.replace("{{SERVICE_NAME}}", target)
    content = content.replace("{{PROFILE}}", profile_name)
    content = content.replace("{{RULES_PIN}}", con.ref if con else "")
    content = content.replace("{{AGENT_SKILLS_REF}}", skill.ref if skill else "")
    content = content.replace("{{AGENT_SKILLS_SLASH_LIST}}", slash_list(skill_names))
    content = content.replace("{{CHECK_COMMAND}}", "")
    content = content.replace("{{TEST_COMMAND}}", "")
    content = content.replace("{{VERIFY_SMOKE}}", "")
    content = content.replace("{{SETUP_NOTES}}", "")
    content = content.replace(
        "`.agents/skills/prayog-skills/` (git submodule",
        "`.agents/skills/<skill>/` (symlinks via `.harness/skills/` hub",
    )

    (repo_path / "AGENTS.md").write_text(content, encoding="utf-8")
    print(f"  ✔  AGENTS.md  ← {tpl_name}")


def _remove_legacy_cursor_skills(repo_path: Path, *, apply: bool) -> None:
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


def _preview_or_resolve_skills(
    prayog_submodule: Path,
    profile: HarnessProfile,
    profile_name: str,
) -> list[str] | None:
    if not prayog_submodule.is_dir():
        print(
            f"    [dry-run] prayog skills: resolve from profiles/{profile.prayog_profile}.yaml "
            f"after submodule pin"
        )
        return None
    return resolve_skill_names(prayog_submodule, profile, profile_name)


def _apply_harness_to_repo(
    repo_path: Path,
    profile: HarnessProfile,
    profile_name: str,
    org: str,
    *,
    target: str,
    meta_repo: str,
    apply: bool = False,
) -> int:
    prayog_submodule = repo_path / PRAYOG_SKILLS_SUBMODULE_REL
    skill_names: list[str] = []
    community_dirs = [spec.submodule_dir for spec in profile.community_skills]
    lane_key = lane_key_for_profile(profile_name)

    if not apply:
        con = profile.constitution
        if con:
            print(f"    [dry-run] constitution submodule: {con.submodule_url}@{con.ref}")
        else:
            print("    [dry-run] constitution: (none — no .cursor/rules submodule for this profile)")
        for skill in profile.skills:
            skill_url = f"https://github.com/{skill.org}/{skill.repo}"
            print(
                f"    [dry-run] skills submodule: {PRAYOG_SKILLS_SUBMODULE_REL} "
                f"← {skill_url}@{skill.ref}"
            )
        install_community_skills(repo_path, profile, apply=False)
        preview = _preview_or_resolve_skills(prayog_submodule, profile, profile_name)
        preview_names = (preview or []) + community_skill_names(profile)
        if preview is not None:
            materialize_skill_tree(
                repo_path,
                prayog_submodule_rel=PRAYOG_SKILLS_SUBMODULE_REL,
                skill_names=preview,
                runtime_roots=profile.skill_runtimes,
                lane_key=lane_key,
                community_submodule_dirs=community_dirs,
                apply=False,
            )
        copy_harness_profile(
            prayog_submodule,
            profile,
            repo_path / HARNESS_PROFILE_REL,
            harness_profile_name=profile_name,
            apply=False,
        )
        _seed_codeowners(repo_path, profile.codeowners_template, org, apply=False)
        _seed_harness_pin(
            repo_path,
            profile.harness_pin_template,
            profile,
            profile_name,
            skill_names=preview_names,
            apply=False,
        )
        _seed_agents_md(
            repo_path,
            profile_name,
            profile,
            skill_names=preview_names,
            target=target,
            org=org,
            meta_repo=meta_repo,
            apply=False,
        )
        return 0

    con = profile.constitution
    if con:
        if pin_submodule(
            repo_path,
            ".cursor/rules",
            con.submodule_url,
            con.ref,
            label="constitution",
        ):
            print(f"  ✔  constitution pinned: {con.repo}@{con.ref}")
        else:
            print(f"  ✗  constitution pin failed: {con.submodule_url}@{con.ref}", file=sys.stderr)
            return 1
    else:
        print("  –  constitution: (none — meta/config repo, no rules submodule)")

    _remove_legacy_cursor_skills(repo_path, apply=True)

    for skill in profile.skills:
        skill_url = f"https://github.com/{skill.org}/{skill.repo}"
        skill_ref = skill.ref or "HEAD"
        if not pin_submodule(
            repo_path,
            PRAYOG_SKILLS_SUBMODULE_REL,
            skill_url,
            skill_ref,
            label=f"skills/{skill.repo}",
        ):
            print(f"  ✗  skills pin failed: {skill_url}@{skill_ref}", file=sys.stderr)
            return 1
        print(f"  ✔  skills pinned: {skill.org}/{skill.repo}@{skill_ref}")

    try:
        skill_names = resolve_skill_names(prayog_submodule, profile, profile_name)
    except HarnessResolveError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    materialized = materialize_skill_tree(
        repo_path,
        prayog_submodule_rel=PRAYOG_SKILLS_SUBMODULE_REL,
        skill_names=skill_names,
        runtime_roots=profile.skill_runtimes,
        lane_key=lane_key,
        community_submodule_dirs=community_dirs,
        apply=True,
    )
    if len(materialized) < len(skill_names):
        print(
            f"  WARN: materialized {len(materialized)}/{len(skill_names)} prayog skills",
            file=sys.stderr,
        )

    copy_harness_profile(
        prayog_submodule,
        profile,
        repo_path / HARNESS_PROFILE_REL,
        harness_profile_name=profile_name,
        apply=True,
    )

    community_names = install_community_skills(repo_path, profile, apply=True)
    all_skill_names = skill_names + community_names

    _seed_codeowners(repo_path, profile.codeowners_template, org, apply=True)
    _seed_harness_pin(
        repo_path,
        profile.harness_pin_template,
        profile,
        profile_name,
        skill_names=all_skill_names,
        apply=True,
    )
    _seed_agents_md(
        repo_path,
        profile_name,
        profile,
        skill_names=all_skill_names,
        target=target,
        org=org,
        meta_repo=meta_repo,
        apply=True,
    )
    return 0


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

    if config_dir is None:
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
        else:
            ws = workspace or Path(".").resolve().parent
            meta_repo = cdir.parent.name
    except SchemaError:
        ws = workspace or Path(".").resolve().parent
        meta_repo = cdir.parent.name

    if meta:
        target = meta_repo
        stack = gov.repos[target].stack if target in gov.repos else PM_HARNESS_PROFILE
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
        print("  Clone it first, then re-run apply-harness.")
        if apply:
            return 1

    result = _apply_harness_to_repo(
        repo_path,
        profile,
        profile_name,
        org,
        target=target,
        meta_repo=meta_repo,
        apply=apply,
    )
    if result != 0:
        return result

    if not apply:
        target_flag = "--meta" if meta else f"--repo {target}"
        print_next_box([f"launchpad apply-harness {target_flag} --apply"])
    else:
        client_id = os.environ.get("LAUNCHPAD_CLIENT", "").strip()
        client_prefix = f"--client {client_id} " if client_id else ""
        target_flag = "--meta" if meta else f"--repo {target}"
        print_next_box([f"launchpad {client_prefix}status {target_flag}".strip()])

    return 0
