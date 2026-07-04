"""Tests for harness config schema (meta block)."""

from __future__ import annotations

import unittest

from launchpad.config import load_harness_config

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
HARNESS_META = ROOT / "tests" / "fixtures" / "harness-meta.yaml"


class HarnessConfigMetaTests(unittest.TestCase):
    def test_load_meta_block(self) -> None:
        cfg = load_harness_config(HARNESS_META)
        self.assertEqual(cfg["org"], "example-org")
        self.assertEqual(cfg["meta"]["profile"], "meta-pm")
        self.assertIn("meta-pm", cfg["profiles"])
        profile = cfg["profiles"]["meta-pm"]
        self.assertIn("community_skills", profile)
        self.assertEqual(profile["community_skills"][0]["skill"], "prd")


if __name__ == "__main__":
    unittest.main()
