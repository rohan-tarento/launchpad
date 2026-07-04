"""Tests for launchpad kit path resolution."""

from __future__ import annotations

import unittest
from pathlib import Path

from launchpad.paths import kit_root

ROOT = Path(__file__).resolve().parents[1]


class KitPathTests(unittest.TestCase):
    def test_kit_root_has_templates(self) -> None:
        root = kit_root()
        self.assertTrue((root / "templates" / "AGENTS.meta.md").is_file())
        self.assertTrue((root / "templates" / "harness-pin.meta.yaml").is_file())

    def test_kit_root_has_playbook(self) -> None:
        root = kit_root()
        self.assertTrue((root / "playbook" / "harness-pins.md").is_file())


if __name__ == "__main__":
    unittest.main()
