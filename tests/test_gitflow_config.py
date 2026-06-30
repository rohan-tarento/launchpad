"""Gitflow config loading tests."""

import tempfile
import unittest
from pathlib import Path

from launchpad.config import load_gitflow_config


class TestGitflowConfig(unittest.TestCase):
    def test_defaults_merge_grant_push_and_read(self) -> None:
        yaml_text = """
apiVersion: launchpad/v1
kind: GitflowConfig
org: example
teams:
  qa: qa-team
defaults:
  grant_push: [qa]
repos:
  api:
    profile: backend
    develop_merge: backend
    grant_read: [qa]
  meta:
    profile: platform
    develop_merge: pm
"""
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
            fh.write(yaml_text)
            path = Path(fh.name)

        try:
            cfg = load_gitflow_config(path)
            api = next(r for r in cfg["repos"] if r["name"] == "api")
            meta = next(r for r in cfg["repos"] if r["name"] == "meta")
            self.assertEqual(api["grant_push"], ["qa"])
            self.assertEqual(api["grant_read"], ["qa"])
            self.assertEqual(meta["grant_push"], ["qa"])
            self.assertEqual(meta["grant_read"], [])
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
