"""Tests for launchpad scaffold command."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from launchpad.scaffold.errors import ScaffoldError
from launchpad.scaffold.profiles import get_profile, list_profiles
from launchpad.scaffold.run import build_context, build_plan, run_scaffold

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_TEMPLATE = ROOT / "tests" / "fixtures" / "scaffold-python-minimal"
HARNESS_FIXTURE = ROOT / "tests" / "fixtures" / "harness-scaffold.yaml"


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
            repo_name="example-api",
            repo_meta={"service_name": "Example API", "scaffold": {"has_kafka": "yes"}},
            cli_options={"has_emqx": "no"},
        )
        self.assertEqual(ctx["service_name"], "example-api")
        self.assertEqual(ctx["service_description"], "Example API")
        self.assertEqual(ctx["has_kafka"], "yes")
        self.assertEqual(ctx["auth_mode"], "jwt")

    def test_rejects_unknown_option(self) -> None:
        profile = get_profile("python-backend")
        with self.assertRaises(ScaffoldError):
            build_context(
                profile,
                repo_name="example-api",
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

    def test_apply_force_overlays_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            existing = workspace / "example-api"
            existing.mkdir()
            (existing / "stale.txt").write_text("keep me", encoding="utf-8")
            git_dir = existing / ".git"
            git_dir.mkdir()
            (git_dir / "HEAD").write_text("ref: refs/heads/develop\n", encoding="utf-8")
            run_scaffold(
                config_path=HARNESS_FIXTURE,
                repo_name="example-api",
                workspace=workspace,
                template=str(FIXTURE_TEMPLATE),
                dry_run=False,
                force=True,
            )
            self.assertTrue((existing / "stale.txt").read_text(encoding="utf-8") == "keep me")
            self.assertTrue((git_dir / "HEAD").is_file())
            self.assertTrue((existing / "README.md").is_file())
            text = (existing / "README.md").read_text(encoding="utf-8")
            self.assertIn("example-api", text)


if __name__ == "__main__":
    unittest.main()
