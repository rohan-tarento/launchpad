"""Generate the root-level skills lockfile for harness-managed Prayog skills."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from launchpad.harness.paths import SKILLS_LOCK_REL
from launchpad.harness.skills_resolve import find_skill_source_dir
from launchpad.schema.harness import HarnessProfile


def write_skills_lock(
    repo_path: Path,
    *,
    prayog_root: Path,
    profile: HarnessProfile,
    skill_names: list[str],
    lane_key: str,
    apply: bool,
) -> bool:
    """Write skills-lock.json using installed skill symlink paths."""
    entries: dict[str, dict[str, str]] = {}
    source = profile.skills[0] if profile.skills else None
    if source is None:
        return False

    for name in skill_names:
        skill_dir = find_skill_source_dir(prayog_root, name, lane_key=lane_key)
        if skill_dir is None:
            continue
        skill_file = skill_dir / "SKILL.md"
        entries[name] = {
            "source": f"{source.org}/{source.repo}",
            "sourceType": "github",
            "skillPath": f".agents/skills/{name}/SKILL.md",
            "computedHash": hashlib.sha256(skill_file.read_bytes()).hexdigest(),
        }

    lock: dict[str, Any] = {"version": 1, "skills": dict(sorted(entries.items()))}
    dest = repo_path / SKILLS_LOCK_REL
    if not apply:
        print(f"    [dry-run] skills lock  →  {SKILLS_LOCK_REL}")
        return True
    dest.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"  ✔  skills lock  →  {SKILLS_LOCK_REL}")
    return True

