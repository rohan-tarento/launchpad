"""Tests for local workspace clone/link after platform seed."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from launchpad.config import resolve_workspace_parent
from launchpad.workspace_clone import (
    github_https_url,
    is_greenfield_link,
    meta_repo_name,
    repo_dest_path,
    run,
)

ROOT = Path(__file__).resolve().parents[1]
TENANT_META = ROOT / "examples" / "tenant-meta"


class WorkspaceParentTests(unittest.TestCase):
    def setUp(self) -> None:
        self._prev = os.environ.get("LAUNCHPAD_TENANT_ROOT")
        os.environ["LAUNCHPAD_TENANT_ROOT"] = str(TENANT_META)

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("LAUNCHPAD_TENANT_ROOT", None)
        else:
            os.environ["LAUNCHPAD_TENANT_ROOT"] = self._prev

    def test_resolve_workspace_parent_relative(self) -> None:
        parent = resolve_workspace_parent(gitflow_options={"workspace": ".."})
        self.assertEqual(parent, TENANT_META.parent)

    def test_repo_dest_paths(self) -> None:
        parent = TENANT_META.parent
        self.assertEqual(
            repo_dest_path("example-api", workspace_parent=parent, meta_repo="example-meta"),
            parent / "example-api",
        )
        self.assertEqual(
            repo_dest_path("example-meta", workspace_parent=parent, meta_repo="example-meta"),
            TENANT_META,
        )


class WorkspaceCloneRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self._prev = os.environ.get("LAUNCHPAD_TENANT_ROOT")

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("LAUNCHPAD_TENANT_ROOT", None)
        else:
            os.environ["LAUNCHPAD_TENANT_ROOT"] = self._prev

    def test_dry_run_lists_gitflow_repos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "example-meta"
            meta.mkdir()
            (meta / ".launchpad-version").write_text("0.3.6\n", encoding="utf-8")
            config_dir = meta / "config"
            config_dir.mkdir()
            for name in ("org-example.yaml", "gitflow-example.yaml"):
                src = TENANT_META / "config" / name
                (config_dir / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

            os.environ["LAUNCHPAD_TENANT_ROOT"] = str(meta)
            client = mock.Mock(dry_run=True)
            with mock.patch("launchpad.workspace_clone.clone_one_repo") as clone_mock:
                run(client, org="example-org", config_path=config_dir / "gitflow-example.yaml")
                self.assertGreater(clone_mock.call_count, 0)
                dests = {call.kwargs["dest"].resolve() for call in clone_mock.call_args_list}
                self.assertIn(meta.resolve(), dests)
                self.assertIn((meta.parent / "example-api").resolve(), dests)

    def test_meta_repo_name_from_gitflow(self) -> None:
        from launchpad.config import load_gitflow_config

        gf = load_gitflow_config(TENANT_META / "config" / "gitflow-example.yaml")
        self.assertEqual(meta_repo_name(gf), "example-meta")

    def test_github_https_url(self) -> None:
        self.assertEqual(github_https_url("example-org", "example-api"), "https://github.com/example-org/example-api.git")

    def test_is_greenfield_link_meta(self) -> None:
        os.environ["LAUNCHPAD_TENANT_ROOT"] = str(TENANT_META)
        self.assertTrue(is_greenfield_link(TENANT_META, repo="example-meta", meta_repo="example-meta"))
        self.assertFalse(
            is_greenfield_link(TENANT_META.parent / "example-api", repo="example-api", meta_repo="example-meta")
        )

    def test_link_meta_uses_prefer_local_in_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "mobbot-meta"
            meta.mkdir()
            (meta / ".launchpad-version").write_text("0.3.6\n", encoding="utf-8")
            (meta / "README.md").write_text("# local meta\n", encoding="utf-8")
            os.environ["LAUNCHPAD_TENANT_ROOT"] = str(meta)
            with mock.patch("launchpad.workspace_clone._run_git") as git_mock:
                from launchpad.workspace_clone import clone_one_repo

                clone_one_repo(
                    org="example-org",
                    repo="mobbot-meta",
                    dest=meta,
                    dry_run=True,
                    check_remote=False,
                    meta_repo="mobbot-meta",
                )
                merge_calls = [c for c in git_mock.call_args_list if c.args[0][0] == "merge"]
                self.assertTrue(merge_calls)
                self.assertIn("-X", merge_calls[0].args[0])
                self.assertIn("ours", merge_calls[0].args[0])


if __name__ == "__main__":
    unittest.main()
