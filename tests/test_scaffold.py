"""Tests for launchpad scaffold command."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from launchpad.scaffold.errors import ScaffoldError
from launchpad.scaffold.profiles import get_profile, list_profiles
from launchpad.scaffold.run import build_context, build_plan, run_scaffold

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_TEMPLATE = ROOT / "tests" / "fixtures" / "scaffold-python-minimal"
HARNESS_FIXTURE = ROOT / "tests" / "fixtures" / "harness-scaffold.yaml"
FOUNDATION = Path.home() / "Workspace" / "handson" / "drivestream" / "python-fastapi-foundation"


class ScaffoldProfileTests(unittest.TestCase):
    def test_python_backend_registered(self) -> None:
        self.assertIn("python-backend", list_profiles(implemented_only=True))

    def test_frontend_not_implemented(self) -> None:
        with self.assertRaises(ScaffoldError):
            build_plan(
                config_path=HARNESS_FIXTURE,
                repo_name="example-api",
                profile_name="frontend",
            )

    def test_nextjs_bff_alias(self) -> None:
        profile = get_profile("nextjs-bff")
        self.assertEqual(profile.name, "frontend")


class ScaffoldContextTests(unittest.TestCase):
    def test_build_context_from_repo_meta(self) -> None:
        profile = get_profile("python-backend")
        ctx = build_context(
            profile,
            repo_name="suchana",
            repo_meta={"service_name": "Suchana", "scaffold": {"has_kafka": "yes"}},
            cli_options={"has_emqx": "no"},
        )
        self.assertEqual(ctx["service_name"], "suchana")
        self.assertEqual(ctx["service_description"], "Suchana")
        self.assertEqual(ctx["has_kafka"], "yes")
        self.assertEqual(ctx["auth_mode"], "jwt")

    def test_rejects_unknown_option(self) -> None:
        profile = get_profile("python-backend")
        with self.assertRaises(ScaffoldError):
            build_context(
                profile,
                repo_name="suchana",
                repo_meta={},
                cli_options={"not_a_real_key": "yes"},
            )


class ScaffoldPlanTests(unittest.TestCase):
    def test_dry_run_plan_uses_fixture_template(self) -> None:
        plan = build_plan(
            config_path=HARNESS_FIXTURE,
            repo_name="example-api",
            template=str(FIXTURE_TEMPLATE),
        )
        self.assertEqual(plan.profile, "python-backend")
        self.assertEqual(plan.repo, "example-api")
        self.assertEqual(plan.template, str(FIXTURE_TEMPLATE.resolve()))
        self.assertEqual(plan.target_dir.name, "example-api")

    def test_unknown_repo_raises(self) -> None:
        with self.assertRaises(ScaffoldError):
            build_plan(config_path=HARNESS_FIXTURE, repo_name="missing-repo")


class ScaffoldApplyTests(unittest.TestCase):
    def test_apply_generates_minimal_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            run_scaffold(
                config_path=HARNESS_FIXTURE,
                repo_name="example-api",
                workspace=workspace,
                template=str(FIXTURE_TEMPLATE),
                dry_run=False,
            )
            readme = workspace / "example-api" / "README.md"
            self.assertTrue(readme.is_file())
            text = readme.read_text(encoding="utf-8")
            self.assertIn("example-api", text)
            self.assertIn("Demo Api", text)

    def test_apply_fails_when_target_exists_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "example-api").mkdir()
            with self.assertRaises(ScaffoldError) as ctx:
                run_scaffold(
                    config_path=HARNESS_FIXTURE,
                    repo_name="example-api",
                    workspace=workspace,
                    template=str(FIXTURE_TEMPLATE),
                    dry_run=False,
                )
            self.assertIn("target already exists", str(ctx.exception))

    def test_apply_force_replaces_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            stale = workspace / "example-api"
            stale.mkdir()
            (stale / "stale.txt").write_text("old", encoding="utf-8")
            run_scaffold(
                config_path=HARNESS_FIXTURE,
                repo_name="example-api",
                workspace=workspace,
                template=str(FIXTURE_TEMPLATE),
                dry_run=False,
                force=True,
            )
            self.assertFalse((stale / "stale.txt").exists())
            self.assertTrue((stale / "README.md").is_file())


@unittest.skipUnless(FOUNDATION.is_dir(), "python-fastapi-foundation not present locally")
class ScaffoldFoundationIntegrationTests(unittest.TestCase):
    def test_suchana_plan_against_real_foundation(self) -> None:
        harness = Path.home() / "Workspace" / "handson" / "drivestream" / "drivestream-meta" / "config" / "harness-autrio10x.yaml"
        if not harness.is_file():
            self.skipTest("drivestream-meta harness config not found")

        plan = build_plan(
            config_path=harness,
            repo_name="suchana",
            template=str(FOUNDATION),
            options={"has_kafka": "yes", "has_postgres": "yes", "parichay_client": "yes"},
        )
        self.assertEqual(plan.profile, "python-backend")
        self.assertEqual(plan.context["service_name"], "suchana")
        self.assertEqual(plan.context["has_kafka"], "yes")
        self.assertTrue(str(plan.template).endswith("python-fastapi-foundation"))

    def test_apply_suchana_smoke(self) -> None:
        harness = Path.home() / "Workspace" / "handson" / "drivestream" / "drivestream-meta" / "config" / "harness-autrio10x.yaml"
        if not harness.is_file():
            self.skipTest("drivestream-meta harness config not found")

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            run_scaffold(
                config_path=harness,
                repo_name="suchana",
                workspace=workspace,
                template=str(FOUNDATION),
                options={"has_kafka": "yes", "has_postgres": "yes"},
                dry_run=False,
            )
            service_dir = workspace / "suchana"
            self.assertTrue((service_dir / "src" / "main.py").is_file())
            self.assertTrue((service_dir / "Makefile").is_file())
            self.assertTrue((service_dir / "tests" / "unit" / "api" / "test_health.py").is_file())


if __name__ == "__main__":
    unittest.main()
