"""Tests for harness rules submodule detection and orphan recovery."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from launchpad.harness import (
    _gitmodules_mentions_path,
    _is_submodule,
    _remove_orphan_gitmodules_entry,
    _submodule_in_index,
)


class HarnessSubmoduleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-b", "develop"], cwd=self.repo, check=True, capture_output=True)
        (self.repo / "README.md").write_text("# test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        self.rel_path = ".cursor/rules"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_orphan_gitmodules(self) -> None:
        (self.repo / ".gitmodules").write_text(
            f'[submodule "{self.rel_path}"]\n'
            f"    path = {self.rel_path}\n"
            f"    url = https://github.com/example-org/rules.git\n",
            encoding="utf-8",
        )

    def test_orphan_gitmodules_is_not_submodule(self) -> None:
        self._write_orphan_gitmodules()
        self.assertTrue(_gitmodules_mentions_path(self.repo, self.rel_path))
        self.assertFalse(_submodule_in_index(self.repo, self.rel_path))
        self.assertFalse(_is_submodule(self.repo, self.rel_path))

    def test_remove_orphan_gitmodules_entry(self) -> None:
        self._write_orphan_gitmodules()
        _remove_orphan_gitmodules_entry(self.repo, self.rel_path, dry_run=False)
        self.assertFalse(_gitmodules_mentions_path(self.repo, self.rel_path))

    def test_remove_orphan_gitmodules_dry_run_leaves_file(self) -> None:
        self._write_orphan_gitmodules()
        _remove_orphan_gitmodules_entry(self.repo, self.rel_path, dry_run=True)
        self.assertTrue(_gitmodules_mentions_path(self.repo, self.rel_path))


if __name__ == "__main__":
    unittest.main()
