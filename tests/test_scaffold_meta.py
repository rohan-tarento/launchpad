"""Tests for scaffold-meta command."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from launchpad.scaffold.errors import ScaffoldError
from launchpad.scaffold.meta_run import build_meta_plan, run_scaffold_meta
from launchpad.scaffold.profiles import list_profiles

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_TEMPLATE = ROOT / "tests" / "fixtures" / "scaffold-meta-minimal"


class ScaffoldMetaProfileTests(unittest.TestCase):
    def test_tenant_meta_registered(self) -> None:
        self.assertIn("tenant-meta", list_profiles(implemented_only=True))


class ScaffoldMetaPlanTests(unittest.TestCase):
    def test_dry_run_plan_uses_fixture_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "kola-meta"
            plan = build_meta_plan(
                meta_repo="kola-meta",
                target_dir=target,
                template=str(FIXTURE_TEMPLATE),
            )
            self.assertEqual(plan.profile, "tenant-meta")
            self.assertEqual(plan.meta_repo, "kola-meta")
            self.assertEqual(plan.template, str(FIXTURE_TEMPLATE.resolve()))


class ScaffoldMetaApplyTests(unittest.TestCase):
    def test_apply_generates_minimal_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "kola-meta"
            run_scaffold_meta(
                meta_repo="kola-meta",
                target_dir=target,
                template=str(FIXTURE_TEMPLATE),
                dry_run=False,
            )
            readme = target / "README.md"
            self.assertTrue(readme.is_file())
            self.assertIn("Example", readme.read_text(encoding="utf-8"))

    def test_force_preserves_prd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "kola-meta"
            target.mkdir()
            prd = target / "prd" / "INIT-KEEP.md"
            prd.parent.mkdir(parents=True)
            prd.write_text("keep me", encoding="utf-8")
            run_scaffold_meta(
                meta_repo="kola-meta",
                target_dir=target,
                template=str(FIXTURE_TEMPLATE),
                dry_run=False,
                force=True,
            )
            self.assertEqual(prd.read_text(encoding="utf-8"), "keep me")
            self.assertTrue((target / "README.md").is_file())

    def test_apply_fails_when_target_exists_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "kola-meta"
            target.mkdir()
            (target / "existing.txt").write_text("x", encoding="utf-8")
            with self.assertRaises(ScaffoldError):
                run_scaffold_meta(
                    meta_repo="kola-meta",
                    target_dir=target,
                    template=str(FIXTURE_TEMPLATE),
                    dry_run=False,
                )


if __name__ == "__main__":
    unittest.main()
