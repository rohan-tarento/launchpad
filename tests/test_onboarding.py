"""Tests for onboarding spec and plan."""

from __future__ import annotations

import unittest
from pathlib import Path

from launchpad.onboarding.errors import OnboardingError
from launchpad.onboarding.plan import build_plan, format_plan
from launchpad.onboarding.spec import load_onboarding_spec, normalize_spec

ROOT = Path(__file__).resolve().parents[1]
KOLA_SPEC = ROOT / "examples" / "onboarding-kola.yaml"
KOLA_GITLAB_SPEC = ROOT / "examples" / "onboarding-kola-gitlab.yaml"


class OnboardingSpecTests(unittest.TestCase):
    def test_load_kola_example(self) -> None:
        spec = load_onboarding_spec(KOLA_SPEC)
        self.assertEqual(spec["client_id"], "kola")
        self.assertEqual(spec["org"], "kola-lab")
        self.assertEqual(spec["forge"]["type"], "github")
        self.assertEqual(len(spec["repos"]), 2)
        self.assertIn("frontend", spec["rules"])

    def test_gitlab_forge_accepted(self) -> None:
        spec = load_onboarding_spec(KOLA_GITLAB_SPEC)
        self.assertEqual(spec["forge"]["type"], "gitlab")

    def test_rejects_meta_in_repos(self) -> None:
        raw = {
            "client_id": "kola",
            "org": "kola-lab",
            "meta_repo": "kola-meta",
            "repos": [{"name": "kola-meta", "profile": "platform"}],
        }
        with self.assertRaises(OnboardingError):
            normalize_spec(raw)

    def test_client_id_validation(self) -> None:
        with self.assertRaises(OnboardingError):
            normalize_spec({"client_id": "KOLA", "org": "x", "repos": [{"name": "a"}]})


class OnboardingPlanTests(unittest.TestCase):
    def test_plan_lists_config_files(self) -> None:
        spec = load_onboarding_spec(KOLA_SPEC)
        plan = build_plan(spec, spec_path=KOLA_SPEC)
        text = format_plan(plan)
        self.assertIn("config/org-kola-lab.yaml", text)
        self.assertIn("config/harness-kola-lab.yaml", text)
        self.assertIn("templates/AGENTS.frontend.md", text)
        self.assertIn("launchpad onboard apply", text)

    def test_gitlab_plan_warning(self) -> None:
        spec = load_onboarding_spec(KOLA_GITLAB_SPEC)
        plan = build_plan(spec, spec_path=KOLA_GITLAB_SPEC)
        self.assertTrue(any("gitlab" in w.lower() for w in plan.warnings))


if __name__ == "__main__":
    unittest.main()
