"""Tests for harness GitHub URL policy (HTTPS-only)."""

from __future__ import annotations

import unittest

from launchpad.harness import HarnessError, _require_github_https_url


class HarnessHttpsUrlTests(unittest.TestCase):
    def test_accepts_https_with_git_suffix(self) -> None:
        url = "https://github.com/example-org/service-rules.git"
        self.assertEqual(_require_github_https_url(url), url)

    def test_accepts_https_without_git_suffix(self) -> None:
        url = "https://github.com/example-org/service-rules"
        self.assertEqual(_require_github_https_url(url), url)

    def test_rejects_ssh_git_at(self) -> None:
        with self.assertRaises(HarnessError) as ctx:
            _require_github_https_url("git@github.com:example-org/service-rules.git")
        self.assertIn("HTTPS", str(ctx.exception))

    def test_rejects_ssh_scheme(self) -> None:
        with self.assertRaises(HarnessError):
            _require_github_https_url("ssh://git@github.com/example-org/service-rules.git")

    def test_rejects_http(self) -> None:
        with self.assertRaises(HarnessError):
            _require_github_https_url("http://github.com/example-org/service-rules.git")

    def test_rejects_non_github(self) -> None:
        with self.assertRaises(HarnessError):
            _require_github_https_url("https://gitlab.com/example-org/service-rules.git")


if __name__ == "__main__":
    unittest.main()
