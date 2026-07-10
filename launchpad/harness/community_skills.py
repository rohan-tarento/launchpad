"""Community agent skills declared in harness YAML."""

from __future__ import annotations

import sys
from pathlib import Path

from launchpad.harness.skills_materialize import materialize_community_skill_tree
from launchpad.harness.submodules import pin_submodule
from launchpad.schema.harness import HarnessProfile


def install_community_skills(
    repo_path: Path,
    profile: HarnessProfile,
    *,
    apply: bool,
) -> list[str]:
    """Pin community skill repos and materialize hub + runtime symlinks."""
    installed: list[str] = []
    for spec in profile.community_skills:
        if not apply:
            print(
                f"    [dry-run] community submodule: {spec.submodule_rel} "
                f"← {spec.url}@{spec.ref}"
            )
            if materialize_community_skill_tree(
                repo_path,
                community_submodule_rel=spec.submodule_rel,
                skill_name=spec.skill,
                runtime_roots=profile.skill_runtimes,
                apply=False,
            ):
                installed.append(spec.skill)
            continue

        if pin_submodule(
            repo_path,
            spec.submodule_rel,
            spec.url,
            spec.ref,
            label=f"community/{spec.submodule_dir}",
        ):
            if materialize_community_skill_tree(
                repo_path,
                community_submodule_rel=spec.submodule_rel,
                skill_name=spec.skill,
                runtime_roots=profile.skill_runtimes,
                apply=True,
            ):
                installed.append(spec.skill)
        else:
            print(
                f"  ✗  community submodule pin failed: {spec.url}@{spec.ref}",
                file=sys.stderr,
            )

    return installed


def community_skill_names(profile: HarnessProfile) -> list[str]:
    return [spec.skill for spec in profile.community_skills]
