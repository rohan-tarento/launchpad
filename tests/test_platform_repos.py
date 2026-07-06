"""Tests for drivestream-lab OSS platform repo constants."""

from __future__ import annotations

import unittest

from launchpad.platform_repos import (
    PLATFORM_ORG,
    gh_cookiecutter_template,
    platform_repo,
    platform_rules_repo,
)


class PlatformReposTests(unittest.TestCase):
    def test_platform_repo(self) -> None:
        self.assertEqual(platform_repo("prayog-skills"), "drivestream-lab/prayog-skills")

    def test_platform_rules_repo(self) -> None:
        self.assertEqual(platform_rules_repo("python"), f"{PLATFORM_ORG}/python-services-rules")
        self.assertEqual(platform_rules_repo("frontend"), f"{PLATFORM_ORG}/nextjs-bff-rules")
        self.assertEqual(platform_rules_repo("data_platform"), f"{PLATFORM_ORG}/data-platform-rules")

    def test_gh_cookiecutter_template(self) -> None:
        self.assertEqual(
            gh_cookiecutter_template("python-backend"),
            "gh:drivestream-lab/python-fastapi-foundation",
        )


if __name__ == "__main__":
    unittest.main()
