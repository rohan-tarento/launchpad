"""Tests for generated Prayog skills lockfiles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from launchpad.harness.skills_lock import write_skills_lock
from launchpad.schema.harness import HarnessProfile

def test_write_skills_lock_uses_installed_paths_and_hashes(tmp_path: Path) -> None:
    prayog = tmp_path / "prayog"
    skill = prayog / "skills" / "development" / "verify"
    skill.mkdir(parents=True)
    content = "# verify\n"
    (skill / "SKILL.md").write_text(content, encoding="utf-8")
    profile = HarnessProfile(
        "python-backend",
        {"skills": [{"repo": "prayog-skills", "ref": "v1"}]},
    )

    assert write_skills_lock(
        tmp_path,
        prayog_root=prayog,
        profile=profile,
        skill_names=["verify"],
        lane_key="development_skills",
        apply=True,
    )

    lock = json.loads((tmp_path / "skills-lock.json").read_text(encoding="utf-8"))
    assert lock == {
        "version": 1,
        "skills": {
            "verify": {
                "source": "drivestream-lab/prayog-skills",
                "sourceType": "github",
                "skillPath": ".agents/skills/verify/SKILL.md",
                "computedHash": hashlib.sha256(content.encode()).hexdigest(),
            }
        },
    }

def test_write_skills_lock_removes_stale_entries_on_apply(tmp_path: Path) -> None:
    """Prove stale/community/unrelated entries are removed on apply."""
    prayog = tmp_path / "prayog"
    skill = prayog / "skills" / "development" / "verify"
    skill.mkdir(parents=True)
    content = "# verify\n"
    (skill / "SKILL.md").write_text(content, encoding="utf-8")
    profile = HarnessProfile(
        "python-backend",
        {"skills": [{"repo": "prayog-skills", "ref": "v1"}]},
    )

    # First, create a lock with stale entries
    stale_lock = {
        "version": 1,
        "skills": {
            "stale-skill": {"source": "old/repo", "sourceType": "github", "skillPath": "old/path/SKILL.md", "computedHash": "abc123"},
            "verify": {"source": "drivestream-lab/prayog-skills", "sourceType": "github", "skillPath": ".agents/skills/verify/SKILL.md", "computedHash": hashlib.sha256(content.encode()).hexdigest()},
            "community-skill": {"source": "community/repo", "sourceType": "github", "skillPath": "community/path/SKILL.md", "computedHash": "def456"},
        },
    }
    (tmp_path / "skills-lock.json").write_text(json.dumps(stale_lock, indent=2) + "\n", encoding="utf-8")

    # Now write a new lock with only the current skill
    assert write_skills_lock(
        tmp_path,
        prayog_root=prayog,
        profile=profile,
        skill_names=["verify"],
        lane_key="development_skills",
        apply=True,
    )

    lock = json.loads((tmp_path / "skills-lock.json").read_text(encoding="utf-8"))
    assert lock == {
        "version": 1,
        "skills": {
            "verify": {
                "source": "drivestream-lab/prayog-skills",
                "sourceType": "github",
                "skillPath": ".agents/skills/verify/SKILL.md",
                "computedHash": hashlib.sha256(content.encode()).hexdigest(),
            }
        },
    }
    # Stale entries should be removed
    assert "stale-skill" not in lock["skills"]
    assert "community-skill" not in lock["skills"]

def test_write_skills_lock_dry_run_preserves_existing_file(tmp_path: Path) -> None:
    """Prove dry-run preserves existing file contents."""
    prayog = tmp_path / "prayog"
    skill = prayog / "skills" / "development" / "verify"
    skill.mkdir(parents=True)
    content = "# verify\n"
    (skill / "SKILL.md").write_text(content, encoding="utf-8")
    profile = HarnessProfile(
        "python-backend",
        {"skills": [{"repo": "prayog-skills", "ref": "v1"}]},
    )

    # Create an existing lock file
    existing_lock = {
        "version": 1,
        "skills": {
            "existing-skill": {"source": "existing/repo", "sourceType": "github", "skillPath": "existing/path/SKILL.md", "computedHash": "xyz789"},
        },
    }
    (tmp_path / "skills-lock.json").write_text(json.dumps(existing_lock, indent=2) + "\n", encoding="utf-8")

    # Dry-run should not modify the file
    assert write_skills_lock(
        tmp_path,
        prayog_root=prayog,
        profile=profile,
        skill_names=["verify"],
        lane_key="development_skills",
        apply=False,
    )

    # Existing lock should be unchanged
    lock = json.loads((tmp_path / "skills-lock.json").read_text(encoding="utf-8"))
    assert lock == existing_lock

