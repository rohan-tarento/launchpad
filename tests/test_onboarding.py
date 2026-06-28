"""Tests for onboarding spec, plan, interview, and apply."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from launchpad.onboarding.apply import run_apply
from launchpad.onboarding.errors import OnboardingError
from launchpad.onboarding.interview import build_spec_from_interview
from launchpad.onboarding.plan import build_plan, format_plan
from launchpad.onboarding.registry import patch_clients_registry, write_secrets_stub
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


class OnboardingInterviewTests(unittest.TestCase):
    def test_build_spec_from_mock_answers(self) -> None:
        answers = iter(
            [
                "kola",
                "KOLA",
                "github",
                "kola-lab",
                "kola-meta",
                "~/Workspace/handson/kola",
                "kola-api",
                "kola-portal",
                "kola-lab/python-services-rules",
                "v0.1.0",
                "kola-lab/nextjs-bff-rules",
                "v0.1.0",
                "y",
                "y",
                "n",
            ]
        )

        def reader(_prompt: str) -> str:
            return next(answers)

        spec = build_spec_from_interview(input_fn=reader)
        self.assertEqual(spec["client_id"], "kola")
        self.assertEqual(len(spec["repos"]), 2)
        self.assertEqual(spec["gitflow"]["branch_naming_mode"], "strict")
        self.assertFalse(spec["registry"]["set_default"])


class OnboardingApplyTests(unittest.TestCase):
    def test_apply_scaffolds_meta(self) -> None:
        spec = load_onboarding_spec(KOLA_SPEC)
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "kola"
            workspace.mkdir()
            spec_path = workspace / "onboarding.yaml"
            spec["paths"]["workspace"] = str(workspace)
            spec["_meta_path"] = str(workspace / "kola-meta")

            from launchpad.onboarding.spec import save_onboarding_spec

            save_onboarding_spec(spec_path, spec)
            spec = load_onboarding_spec(spec_path)

            with mock.patch.dict(os.environ, {"HOME": tmp}):
                run_apply(
                    spec,
                    spec_path=spec_path,
                    skip_registry=False,
                    skip_doctor=True,
                )

            meta = workspace / "kola-meta"
            self.assertTrue((meta / "config/org-kola-lab.yaml").is_file())
            self.assertTrue((meta / "config/harness-kola-lab.yaml").is_file())
            self.assertTrue((meta / "templates/AGENTS.python.md").is_file())
            self.assertTrue((meta / "playbook/README.md").is_file())
            self.assertIn("kola-lab", (meta / "config/org-kola-lab.yaml").read_text())

    def test_registry_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            clients = home / ".config" / "launchpad" / "clients.yaml"
            with mock.patch("launchpad.onboarding.registry.CLIENTS_FILE", clients), mock.patch(
                "launchpad.onboarding.registry.CONFIG_DIR", clients.parent
            ), mock.patch("launchpad.onboarding.registry.ENV_D_DIR", home / ".config" / "launchpad" / "env.d"):
                patch_clients_registry(
                    client_id="kola",
                    meta_path=Path("/tmp/kola-meta"),
                    forge_type="github",
                )
                write_secrets_stub(client_id="kola", forge_type="github")
                self.assertIn("kola", clients.read_text())
                env_file = home / ".config" / "launchpad" / "env.d" / "kola.env"
                self.assertTrue(env_file.is_file())
                self.assertIn("GITHUB_TOKEN", env_file.read_text())


if __name__ == "__main__":
    unittest.main()
