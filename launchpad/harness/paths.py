"""Canonical paths for harness skill materialization."""

from __future__ import annotations

PRAYOG_SKILLS_SUBMODULE_REL = "prayog-skills"
SKILLS_LOCK_REL = "skills-lock.json"
HARNESS_SKILLS_HUB_REL = ".harness/skills"
HARNESS_COMMUNITY_REL = ".harness/community"
HARNESS_PROFILE_REL = ".harness/profile.yaml"

DEFAULT_SKILL_RUNTIMES: tuple[str, ...] = (".agents/skills", ".claude/skills")

PM_HARNESS_PROFILE = "meta-pm"
