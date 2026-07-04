"""Tests for harness pin parsing in verify."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from launchpad.harness import _harness_pin_ref, _load_harness_pin


class HarnessPinParseTests(unittest.TestCase):
    def test_quoted_agent_skills_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".harness-pin.yaml").write_text(
                "agent_skills:\n  ref: \"v0.3.0\"\n",
                encoding="utf-8",
            )
            pin = _load_harness_pin(repo)
            self.assertEqual(_harness_pin_ref(pin, "agent_skills", "ref"), "v0.3.0")

    def test_unquoted_rules_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".harness-pin.yaml").write_text(
                "rules:\n  ref: v1.0.0\n",
                encoding="utf-8",
            )
            pin = _load_harness_pin(repo)
            self.assertEqual(_harness_pin_ref(pin, "rules", "ref"), "v1.0.0")


if __name__ == "__main__":
    unittest.main()
