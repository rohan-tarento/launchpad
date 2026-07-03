"""Tests for service catalog generation and merge."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from launchpad.onboarding.context import OnboardingContext
from launchpad.onboarding.render import render_service_catalog_config
from launchpad.onboarding.spec import load_onboarding_spec
from launchpad.service_catalog import (
    entries_from_gitflow,
    entries_from_onboarding_spec,
    load_service_catalog,
    merge_service_entries,
    render_service_catalog,
    suggest_branch_code,
    sync_catalog_content,
)

ROOT = Path(__file__).resolve().parents[1]
KOLA_SPEC = ROOT / "examples" / "onboarding-kola.yaml"
TENANT_META = ROOT / "examples" / "tenant-meta"


class ServiceCatalogHelperTests(unittest.TestCase):
    def test_suggest_branch_code(self) -> None:
        self.assertEqual(suggest_branch_code("example-meta", meta_repo="example-meta"), "META")
        self.assertEqual(suggest_branch_code("kola-api"), "API")
        self.assertEqual(suggest_branch_code("kola-portal"), "PORTAL")


class ServiceCatalogOnboardingTests(unittest.TestCase):
    def test_entries_from_onboarding_spec(self) -> None:
        spec = load_onboarding_spec(KOLA_SPEC)
        services = entries_from_onboarding_spec(spec)
        names = [s["name"] for s in services]
        self.assertEqual(names[0], "kola-meta")
        self.assertIn("kola-api", names)
        self.assertIn("kola-portal", names)
        meta = services[0]
        self.assertEqual(meta["branch_code"], "META")
        self.assertEqual(meta["team"], "platform-devs")

    def test_onboarding_render_includes_catalog(self) -> None:
        spec = load_onboarding_spec(KOLA_SPEC)
        ctx = OnboardingContext(spec=spec)
        text = render_service_catalog_config(ctx)
        self.assertIn("kind: ServiceCatalog", text)
        self.assertIn("kola-api", text)
        self.assertIn("branch_code: API", text)


class ServiceCatalogGitflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self._prev = os.environ.get("LAUNCHPAD_TENANT_ROOT")
        os.environ["LAUNCHPAD_TENANT_ROOT"] = str(TENANT_META)

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("LAUNCHPAD_TENANT_ROOT", None)
        else:
            os.environ["LAUNCHPAD_TENANT_ROOT"] = self._prev

    def test_entries_from_gitflow_example(self) -> None:
        from launchpad.config import load_gitflow_config

        gf = load_gitflow_config(TENANT_META / "config" / "gitflow-example.yaml")
        services = entries_from_gitflow(gf, meta_repo="example-meta")
        names = [s["name"] for s in services]
        self.assertEqual(names, ["example-meta", "example-api", "example-registry"])
        self.assertEqual(services[0]["branch_code"], "META")
        self.assertEqual(services[1]["team"], "backend-devs")


class ServiceCatalogMergeTests(unittest.TestCase):
    def test_merge_preserves_curated_fields(self) -> None:
        existing = [
            {
                "name": "example-api",
                "repo": "example-org/example-api",
                "team": "backend-devs",
                "branch_code": "SVC",
                "description": "Curated API description",
                "owns": ["user profiles"],
                "depends_on": ["example-registry"],
            }
        ]
        desired = [
            {
                "name": "example-api",
                "repo": "example-org/example-api",
                "team": "backend-devs",
                "branch_code": "API",
                "description": "example-api — update description in service-catalog-<org>.yaml",
                "owns": [],
                "depends_on": [],
            },
            {
                "name": "example-new",
                "repo": "example-org/example-new",
                "team": "backend-devs",
                "branch_code": "NEW",
                "description": "new service",
                "owns": [],
                "depends_on": [],
            },
        ]
        merged = merge_service_entries(existing, desired)
        api = next(s for s in merged if s["name"] == "example-api")
        self.assertEqual(api["branch_code"], "SVC")
        self.assertEqual(api["description"], "Curated API description")
        self.assertEqual(api["owns"], ["user profiles"])
        self.assertEqual(api["depends_on"], ["example-registry"])
        self.assertIn("example-new", [s["name"] for s in merged])

    def test_sync_merges_with_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "config"
            config_dir.mkdir()
            catalog_path = config_dir / "service-catalog-example.yaml"
            catalog_path.write_text(
                render_service_catalog(
                    org="example-org",
                    services=[
                        {
                            "name": "example-api",
                            "repo": "example-org/example-api",
                            "team": "backend-devs",
                            "branch_code": "SVC",
                            "description": "Curated",
                            "owns": ["auth"],
                            "depends_on": [],
                        }
                    ],
                ),
                encoding="utf-8",
            )
            gf_path = TENANT_META / "config" / "gitflow-example.yaml"
            content, merged = sync_catalog_content(
                org="example-org",
                gitflow_path=gf_path,
                existing_path=catalog_path,
            )
            catalog_path.write_text(content, encoding="utf-8")
            loaded = load_service_catalog(catalog_path)
            api = next(s for s in loaded["services"] if s["name"] == "example-api")
            self.assertEqual(api["branch_code"], "SVC")
            self.assertEqual(api["owns"], ["auth"])
            self.assertIn("example-meta", [s["name"] for s in merged])


if __name__ == "__main__":
    unittest.main()
