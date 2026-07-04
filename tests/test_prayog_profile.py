"""Tests for prayog-skills profile resolution (SSOT @ ref)."""

from __future__ import annotations

import unittest
from pathlib import Path

from launchpad.prayog_profile import (
    discover_skill_paths,
    meta_pm_skill_names_from_tree,
    resolve_agent_skills,
    skill_names_for_profile,
)

ROOT = Path(__file__).resolve().parents[1]
PRAYOG = ROOT / "tests" / "fixtures" / "prayog-v030"


class PrayogProfileTests(unittest.TestCase):
    def test_python_backend_profile_skills(self) -> None:
        names = skill_names_for_profile(PRAYOG, "python-backend")
        self.assertEqual(
            names,
            [
                "spec-draft",
                "initiative-feasibility",
                "spec-technical-review",
                "spec-implementation-plan",
                "pre-implement",
                "loop-spec",
                "ground-spec",
                "verify",
            ],
        )

    def test_meta_pm_tree_convention_includes_prd_impact_map(self) -> None:
        names = meta_pm_skill_names_from_tree(PRAYOG)
        self.assertIn("prd-impact-map", names)
        self.assertIn("validate-requirements", names)
        self.assertNotIn("generate-work-manifest", names)
        self.assertEqual(len(names), 4)

    def test_discover_skill_paths(self) -> None:
        paths = discover_skill_paths(PRAYOG)
        self.assertEqual(
            paths["verify"],
            "skills/development/verify/SKILL.md",
        )
        self.assertEqual(
            paths["prd-impact-map"],
            "skills/requirements/prd-impact-map/SKILL.md",
        )

    def test_resolve_agent_skills_meta_pm(self) -> None:
        resolved = resolve_agent_skills(
            {
                "repo": "drivestream-lab/prayog-skills",
                "ref": "v0.3.0",
                "profile": "meta-pm",
            },
            harness_profile_name="meta-pm",
            prayog_root=PRAYOG,
        )
        self.assertIn("prd-impact-map", resolved["skills"])
        self.assertIn("prd-impact-map", resolved["skill_paths"])

    def test_explicit_skills_override(self) -> None:
        resolved = resolve_agent_skills(
            {
                "ref": "v0.3.0",
                "skills": ["verify"],
            },
            harness_profile_name="python-backend",
            prayog_root=PRAYOG,
        )
        self.assertEqual(resolved["skills"], ["verify"])
        self.assertEqual(
            resolved["skill_paths"]["verify"],
            "skills/development/verify/SKILL.md",
        )


if __name__ == "__main__":
    unittest.main()
