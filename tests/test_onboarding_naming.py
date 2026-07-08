"""Tests for onboarding project slug and repo prefix."""

from __future__ import annotations

import unittest

from launchpad.onboarding.errors import OnboardingError
from launchpad.onboarding.naming import prefixed_repo_name
from launchpad.onboarding.spec import normalize_spec


class OnboardingNamingTests(unittest.TestCase):
    def test_repo_suffix_expands_with_prefix(self) -> None:
        spec = normalize_spec(
            {
                "client_id": "kola",
                "project_slug": "kola",
                "repo_prefix": "kola",
                "org": "apex-common",
                "repos": [
                    {"suffix": "api", "profile": "backend"},
                    {"suffix": "portal", "profile": "frontend"},
                ],
            }
        )
        names = [r["name"] for r in spec["repos"]]
        self.assertEqual(names, ["kola-api", "kola-portal"])
        self.assertEqual(spec["meta_repo"], "kola-meta")
        self.assertEqual(spec["project_slug"], "kola")
        self.assertEqual(spec["repo_prefix"], "kola")

    def test_repos_mapping_form(self) -> None:
        spec = normalize_spec(
            {
                "client_id": "kola",
                "org": "apex-common",
                "repos": {
                    "prefix": "kola",
                    "apps": [
                        {"suffix": "registry", "profile": "backend"},
                    ],
                },
            }
        )
        self.assertEqual(spec["repos"][0]["name"], "kola-registry")
        self.assertEqual(spec["repo_prefix"], "kola")

    def test_full_repo_names_still_work(self) -> None:
        spec = normalize_spec(
            {
                "client_id": "kola",
                "org": "apex-common",
                "repos": [{"name": "kola-api", "profile": "backend"}],
            }
        )
        self.assertEqual(spec["repos"][0]["name"], "kola-api")
        self.assertEqual(spec["project_slug"], "kola")

    def test_org_independent_of_project_slug(self) -> None:
        spec = normalize_spec(
            {
                "client_id": "kola",
                "project_slug": "kola",
                "org": "apex-common",
                "repos": [{"suffix": "api", "profile": "backend"}],
            }
        )
        self.assertEqual(spec["org"], "apex-common")
        self.assertEqual(spec["repos"][0]["name"], "kola-api")
        self.assertEqual(spec["_org_config"], "org-apex-common.yaml")

    def test_rejects_name_and_suffix_together(self) -> None:
        with self.assertRaises(OnboardingError):
            normalize_spec(
                {
                    "client_id": "kola",
                    "org": "apex-common",
                    "repos": [{"name": "kola-api", "suffix": "api", "profile": "backend"}],
                }
            )

    def test_prefixed_repo_name_idempotent(self) -> None:
        self.assertEqual(prefixed_repo_name("kola", "api"), "kola-api")
        self.assertEqual(prefixed_repo_name("kola", "kola-api"), "kola-api")

    def test_validate_registry_id_rejects_uppercase_org_name(self) -> None:
        from launchpad.onboarding.naming import validate_registry_id

        with self.assertRaises(OnboardingError) as ctx:
            validate_registry_id("Apex-Common", field="client_id")
        self.assertIn("not the GitHub org", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
