"""Render context derived from OnboardingSpec."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OnboardingContext:
    spec: dict[str, Any]

    @property
    def client_id(self) -> str:
        return self.spec["client_id"]

    @property
    def display_name(self) -> str:
        return self.spec["display_name"]

    @property
    def org(self) -> str:
        return self.spec["org"]

    @property
    def meta_repo(self) -> str:
        return self.spec["meta_repo"]

    @property
    def forge_type(self) -> str:
        return self.spec["forge"]["type"]

    @property
    def forge_host(self) -> str:
        if self.forge_type == "gitlab":
            return "https://gitlab.com"
        return "https://github.com"

    @property
    def launchpad_playbook_base(self) -> str:
        return "https://github.com/drivestream-lab/launchpad/tree/main/playbook"

    @property
    def meta_playbook_url(self) -> str:
        if self.forge_type == "gitlab":
            return f"{self.forge_host}/{self.org}/{self.meta_repo}/-/tree/main/playbook"
        return f"https://github.com/{self.org}/{self.meta_repo}/tree/main/playbook"

    @property
    def board_url(self) -> str:
        url = self.spec["overrides"].get("board_url") or ""
        if url:
            return url
        if self.forge_type == "github":
            return f"https://github.com/orgs/{self.org}/projects"
        return f"{self.forge_host}/groups/{self.org}/-/boards"

    def rules_git_url(self, repo: str) -> str:
        if self.forge_type == "gitlab":
            return f"{self.forge_host}/{repo}.git"
        return f"https://github.com/{repo}.git"

    def team_slug(self, role: str) -> str:
        mapping = {
            "pm": "pm-team",
            "backend": "backend-devs",
            "frontend": "frontend-devs",
            "platform": "platform-devs",
            "data_platform": "data-platform-devs",
            "release_managers": "release-managers",
            "qa": "qa-team",
            "pe": "pe-team",
        }
        slugs = {t["slug"] for t in self.spec["teams"]}
        preferred = mapping.get(role, role)
        if preferred in slugs:
            return preferred
        return next(iter(slugs), preferred)

    def org_at_team(self, role: str) -> str:
        return f"@{self.org}/{self.team_slug(role)}" if self.forge_type == "gitlab" else f"@{self.org}/{self.team_slug(role)}"
