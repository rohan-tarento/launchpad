"""Tests for universal repo seeding."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from launchpad.gitflow_policy import normalize_gitflow_policy
from launchpad.onboarding.context import OnboardingContext
from launchpad.onboarding.render import render_platform_config
from launchpad.onboarding.spec import load_onboarding_spec
from launchpad.repo_seed import factory_app_repo_names

ROOT = Path(__file__).resolve().parents[1]
KOLA_SPEC = ROOT / "examples" / "onboarding-kola.yaml"


class RepoSeedPolicyTests(unittest.TestCase):
    def test_seed_empty_default_true(self) -> None:
        policy = normalize_gitflow_policy({"options": {}})
        self.assertTrue(policy["options"]["seed_empty"])

    def test_init_empty_alias(self) -> None:
        policy = normalize_gitflow_policy({"options": {"init_empty": True}})
        self.assertTrue(policy["options"]["seed_empty"])


class RepoSeedMetaDetectionTests(unittest.TestCase):
    def test_meta_not_in_org_repos(self) -> None:
        cfg = {
            "org_config": {"repo_names": ["example-api"]},
            "repo_names": ["example-meta", "example-api"],
        }
        app = factory_app_repo_names(cfg)
        self.assertEqual(app, {"example-api"})
        meta = [r for r in cfg["repo_names"] if r not in app]
        self.assertEqual(meta, ["example-meta"])


class PlatformManifestTests(unittest.TestCase):
    def test_onboarding_platform_includes_seed_repos(self) -> None:
        spec = load_onboarding_spec(KOLA_SPEC)
        ctx = OnboardingContext(spec)
        text = render_platform_config(ctx)
        self.assertIn("seed-repos", text)
        self.assertIn("seed", text)


class BootstrapReposUnionTests(unittest.TestCase):
    def test_repos_for_bootstrap_includes_gitflow_meta(self) -> None:
        from launchpad.bootstrap_org import _repos_for_bootstrap
        from launchpad.config import load_org_config

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "org-example.yaml").write_text(
                """
apiVersion: launchpad/v1
kind: OrgConfig
org: example
repos:
  - name: example-api
    private: true
labels: []
teams: []
""",
                encoding="utf-8",
            )
            (root / "gitflow-example.yaml").write_text(
                """
apiVersion: launchpad/v1
kind: GitflowConfig
org: example
includes:
  org: org-example.yaml
teams:
  pm: pm-team
  release_managers: release-managers
  backend: backend-devs
profiles:
  backend: backend
  platform: platform
repos:
  example-meta:
    profile: platform
    develop_merge: pm
  example-api:
    profile: backend
options:
  seed_empty: true
""",
                encoding="utf-8",
            )
            org_cfg = load_org_config(root / "org-example.yaml")
            repos = _repos_for_bootstrap(root / "org-example.yaml", org_cfg)
            names = {r["name"] for r in repos}
            self.assertEqual(names, {"example-api", "example-meta"})


if __name__ == "__main__":
    unittest.main()
