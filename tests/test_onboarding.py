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
from launchpad.onboarding.paths import default_workspace_parent
from launchpad.onboarding.spec import load_onboarding_spec, normalize_spec

ROOT = Path(__file__).resolve().parents[1]
KOLA_SPEC = ROOT / "examples" / "onboarding-kola.yaml"
KOLA_GITLAB_SPEC = ROOT / "examples" / "onboarding-kola-gitlab.yaml"


class OnboardingSpecTests(unittest.TestCase):
    def test_load_kola_example(self) -> None:
        spec = load_onboarding_spec(KOLA_SPEC)
        self.assertEqual(spec["client_id"], "kola")
        self.assertEqual(spec["org"], "apex-common")
        self.assertEqual(spec["forge"]["type"], "github")
        self.assertEqual(len(spec["repos"]), 2)
        self.assertIn("frontend", spec["rules"])
        team_slugs = {t["slug"] for t in spec["teams"]}
        self.assertIn("qa-team", team_slugs)
        self.assertIn("pe-team", team_slugs)

    def test_gitlab_forge_accepted(self) -> None:
        spec = load_onboarding_spec(KOLA_GITLAB_SPEC)
        self.assertEqual(spec["forge"]["type"], "gitlab")

    def test_rejects_meta_in_repos(self) -> None:
        raw = {
            "client_id": "kola",
            "org": "apex-common",
            "meta_repo": "kola-meta",
            "repos": [{"name": "kola-meta", "profile": "platform"}],
        }
        with self.assertRaises(OnboardingError):
            normalize_spec(raw)

    def test_client_id_validation(self) -> None:
        with self.assertRaises(OnboardingError):
            normalize_spec({"client_id": "KOLA", "org": "x", "repos": [{"name": "a"}]})

    def test_default_rules_use_platform_org(self) -> None:
        spec = normalize_spec(
            {
                "client_id": "acme",
                "org": "acme-org",
                "repos": [{"name": "acme-api", "profile": "backend"}],
            }
        )
        self.assertEqual(spec["rules"]["python"]["repo"], "drivestream-lab/python-services-rules")
        self.assertEqual(spec["agent_skills"]["repo"], "drivestream-lab/prayog-skills")

    def test_workspace_defaults_to_spec_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp) / "kola"
            spec_dir.mkdir()
            spec = normalize_spec(
                {
                    "client_id": "kola",
                    "org": "apex-common",
                    "repos": [{"suffix": "api", "profile": "backend"}],
                },
                spec_dir=spec_dir,
            )
            self.assertEqual(spec["paths"]["workspace"], str(spec_dir.resolve()))
            self.assertEqual(spec["_meta_path"], str((spec_dir / "kola-meta").resolve()))

    def test_load_spec_without_workspace_uses_spec_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "kola"
            workspace.mkdir()
            spec_path = workspace / "onboarding.yaml"
            spec_path.write_text(
                "client_id: kola\n"
                "org: apex-common\n"
                "repos:\n"
                "  - suffix: api\n"
                "    profile: backend\n",
                encoding="utf-8",
            )
            spec = load_onboarding_spec(spec_path)
            self.assertEqual(spec["paths"]["workspace"], str(workspace.resolve()))


class OnboardingPlanTests(unittest.TestCase):
    def test_plan_lists_config_files(self) -> None:
        spec = load_onboarding_spec(KOLA_SPEC)
        plan = build_plan(spec, spec_path=KOLA_SPEC)
        text = format_plan(plan)
        self.assertIn("config/org-apex-common.yaml", text)
        self.assertIn("config/harness-apex-common.yaml", text)
        self.assertIn("config/service-catalog-apex-common.yaml", text)
        self.assertIn("templates/AGENTS.md", text)
        self.assertIn("launchpad onboard apply", text)

    def test_gitlab_plan_warning(self) -> None:
        spec = load_onboarding_spec(KOLA_GITLAB_SPEC)
        plan = build_plan(spec, spec_path=KOLA_GITLAB_SPEC)
        self.assertTrue(any("gitlab" in w.lower() for w in plan.warnings))


class OnboardingInterviewTests(unittest.TestCase):
    def test_interview_defaults_workspace_to_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "kola"
            cwd.mkdir()
            answers = iter(
                [
                    "kola",
                    "",
                    "KOLA",
                    "github",
                    "apex-common",
                    "",
                    "",
                    "",
                    "api",
                    "portal",
                    "drivestream-lab/python-services-rules",
                    "v0.1.0",
                    "drivestream-lab/nextjs-bff-rules",
                    "v0.1.0",
                    "n",
                    "n",
                ]
            )

            def reader(_prompt: str) -> str:
                return next(answers)

            with mock.patch("launchpad.onboarding.interview.default_workspace_parent") as mock_ws:
                mock_ws.return_value = cwd.resolve()
                spec = build_spec_from_interview(input_fn=reader)
            self.assertEqual(spec["paths"]["workspace"], str(cwd.resolve()))
            self.assertEqual(spec["org"], "apex-common")
            self.assertEqual(spec["repos"][0]["name"], "kola-api")
            self.assertEqual(spec["meta_repo"], "kola-meta")

    def test_build_spec_from_mock_answers(self) -> None:
        answers = iter(
            [
                "kola",
                "",
                "KOLA",
                "github",
                "apex-common",
                "",
                "kola-meta",
                "~/Workspace/handson/kola",
                "api",
                "portal",
                "drivestream-lab/python-services-rules",
                "v0.1.0",
                "drivestream-lab/nextjs-bff-rules",
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
        self.assertEqual(spec["repos"][0]["name"], "kola-api")
        self.assertEqual(spec["repos"][1]["name"], "kola-portal")
        self.assertEqual(len(spec["repos"]), 2)
        self.assertEqual(spec["gitflow"]["branch_naming_mode"], "strict")
        self.assertFalse(spec["registry"]["set_default"])
        team_slugs = {t["slug"] for t in spec["teams"]}
        self.assertIn("qa-team", team_slugs)
        self.assertIn("pe-team", team_slugs)


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
            self.assertTrue((meta / "config/org-apex-common.yaml").is_file())
            self.assertTrue((meta / "config/harness-apex-common.yaml").is_file())
            self.assertTrue((meta / "templates/AGENTS.md").is_file())
            self.assertTrue((meta / "playbook/README.md").is_file())
            harness_text = (meta / "config/harness-apex-common.yaml").read_text()
            self.assertIn("meta:", harness_text)
            self.assertIn("meta-pm:", harness_text)
            self.assertIn("profile: meta-pm", harness_text)
            self.assertIn("community_skills", harness_text)
            self.assertNotIn("skill_paths:", harness_text)
            org_text = (meta / "config/org-apex-common.yaml").read_text()
            self.assertIn("qa-team", org_text)
            self.assertIn("pe-team", org_text)
            gitflow_text = (meta / "config/gitflow-apex-common.yaml").read_text()
            self.assertIn("qa: qa-team", gitflow_text)
            self.assertIn("pe: pe-team", gitflow_text)
            self.assertIn("grant_push:", gitflow_text)
            self.assertFalse((meta / "prd" / "README.md").is_file())
            self.assertFalse((meta / "work" / "INIT-EXAMPLE-001.yaml").is_file())

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
                write_secrets_stub(
                    client_id="kola",
                    forge_type="github",
                    meta_path=Path("/tmp/kola-meta"),
                )
                self.assertIn("kola", clients.read_text())
                env_file = home / ".config" / "launchpad" / "env.d" / "kola.env"
                self.assertTrue(env_file.is_file())
                self.assertIn("GITHUB_TOKEN", env_file.read_text())
                self.assertIn("LAUNCHPAD_TENANT_ROOT=/tmp/kola-meta", env_file.read_text())


if __name__ == "__main__":
    unittest.main()
