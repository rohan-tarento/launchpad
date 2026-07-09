"""GitHub implementation of ForgeProvider.

Delegates to github_ops for idempotent REST + GraphQL operations.
"""

from __future__ import annotations

from launchpad import github_ops as gh
from launchpad.github_client import GitHubClient


class GitHubForgeProvider:
    """GitHub ForgeProvider backed by GitHubClient."""

    def __init__(self, *, dry_run: bool = True) -> None:
        self._dry_run = dry_run
        self._client: GitHubClient | None = None

    def __enter__(self) -> "GitHubForgeProvider":
        self._client = GitHubClient(dry_run=self._dry_run).__enter__()
        return self

    def __exit__(self, *args: object) -> None:
        if self._client:
            self._client.__exit__(*args)
            self._client = None

    @property
    def client(self) -> GitHubClient:
        if self._client is None:
            raise RuntimeError("GitHubForgeProvider must be used as a context manager")
        return self._client

    def _effective_dry_run(self, dry_run: bool | None) -> bool:
        return self._dry_run if dry_run is None else dry_run

    # ── Teams ────────────────────────────────────────────────────────────────

    def ensure_team(
        self,
        org: str,
        name: str,
        *,
        description: str = "",
        privacy: str = "closed",
        dry_run: bool | None = None,
    ) -> None:
        dr = self._effective_dry_run(dry_run)
        if dr:
            print(f"  [dry-run] ensure team: {org}/{name}")
            return
        gh.ensure_team(self.client, org, name, description=description, privacy=privacy)

    # ── Repos ────────────────────────────────────────────────────────────────

    def ensure_repo(
        self,
        org: str,
        name: str,
        *,
        description: str = "",
        visibility: str = "private",
        dry_run: bool | None = None,
    ) -> None:
        dr = self._effective_dry_run(dry_run)
        if dr:
            print(f"  [dry-run] ensure repo: {org}/{name} ({visibility})")
            return
        gh.ensure_repo(
            self.client,
            org,
            name,
            description=description,
            private=(visibility == "private"),
        )

    def add_team_to_repo(
        self,
        org: str,
        repo: str,
        team: str,
        *,
        permission: str = "push",
        dry_run: bool | None = None,
    ) -> None:
        dr = self._effective_dry_run(dry_run)
        if dr:
            print(f"  [dry-run] add team {team} → {org}/{repo} ({permission})")
            return
        gh.add_team_to_repo(self.client, org, repo, team, permission=permission)

    # ── Branch protection / gitflow ───────────────────────────────────────────

    def ensure_default_branch(
        self, org: str, repo: str, branch: str, *, dry_run: bool | None = None
    ) -> None:
        dr = self._effective_dry_run(dry_run)
        if dr:
            print(f"  [dry-run] ensure default branch: {org}/{repo}@{branch}")
            return
        gh.set_default_branch(self.client, org, repo, branch)

    def ensure_branch(
        self,
        org: str,
        repo: str,
        branch: str,
        *,
        from_branch: str,
        dry_run: bool | None = None,
    ) -> None:
        dr = self._effective_dry_run(dry_run)
        if dr:
            print(f"  [dry-run] ensure branch: {org}/{repo}@{branch} from {from_branch}")
            return
        gh.ensure_branch(self.client, org, repo, branch, from_branch=from_branch)

    def ensure_branch_protection(
        self,
        org: str,
        repo: str,
        branch: str,
        *,
        required_approvals: int = 1,
        dismiss_stale: bool = True,
        dry_run: bool | None = None,
    ) -> None:
        dr = self._effective_dry_run(dry_run)
        if dr:
            print(f"  [dry-run] ensure branch protection: {org}/{repo}@{branch}")
            return
        gh.update_branch_protection(
            self.client,
            org,
            repo,
            branch,
            required_approvals=required_approvals,
            dismiss_stale=dismiss_stale,
        )

    # ── Project board ─────────────────────────────────────────────────────────

    def ensure_project_board(
        self,
        org: str,
        name: str,
        *,
        dry_run: bool | None = None,
    ) -> str:
        dr = self._effective_dry_run(dry_run)
        if dr:
            print(f"  [dry-run] ensure project board: {org} / {name!r}")
            return "dry-run-node-id"
        return gh.ensure_org_project(self.client, org, name)

    def link_repo_to_project(
        self,
        org: str,
        repo: str,
        project_id: str,
        *,
        dry_run: bool | None = None,
    ) -> None:
        dr = self._effective_dry_run(dry_run)
        if dr:
            print(f"  [dry-run] link {org}/{repo} → project {project_id}")
            return
        gh.link_repo_to_project(self.client, org, repo, project_id)
