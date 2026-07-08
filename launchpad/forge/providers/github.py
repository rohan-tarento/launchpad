"""GitHub implementation of ForgeProvider.

Delegates to GitHubClient for actual API calls.
All operations are idempotent — safe to re-run after a partial failure.
"""

from __future__ import annotations

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
        dr = self._dry_run if dry_run is None else dry_run
        if dr:
            print(f"  [dry-run] ensure team: {org}/{name}")
            return
        from launchpad import bootstrap_teams as bt
        bt.ensure_team(self.client, org=org, name=name, description=description, privacy=privacy)

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
        dr = self._dry_run if dry_run is None else dry_run
        if dr:
            print(f"  [dry-run] ensure repo: {org}/{name} ({visibility})")
            return
        from launchpad import bootstrap_org as bo
        bo.ensure_repo(self.client, org=org, name=name, description=description, private=(visibility == "private"))

    def add_team_to_repo(
        self,
        org: str,
        repo: str,
        team: str,
        *,
        permission: str = "push",
        dry_run: bool | None = None,
    ) -> None:
        dr = self._dry_run if dry_run is None else dry_run
        if dr:
            print(f"  [dry-run] add team {team} → {org}/{repo} ({permission})")
            return
        self.client.add_team_to_repo(org=org, repo=repo, team_slug=team, permission=permission)

    # ── Branch protection / gitflow ───────────────────────────────────────────

    def ensure_default_branch(
        self, org: str, repo: str, branch: str, *, dry_run: bool | None = None
    ) -> None:
        dr = self._dry_run if dry_run is None else dry_run
        if dr:
            print(f"  [dry-run] ensure default branch: {org}/{repo}@{branch}")
            return
        self.client.set_default_branch(org=org, repo=repo, branch=branch)

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
        dr = self._dry_run if dry_run is None else dry_run
        if dr:
            print(f"  [dry-run] ensure branch protection: {org}/{repo}@{branch}")
            return
        self.client.update_branch_protection(
            org=org,
            repo=repo,
            branch=branch,
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
        dr = self._dry_run if dry_run is None else dry_run
        if dr:
            print(f"  [dry-run] ensure project board: {org} / {name!r}")
            return "dry-run-node-id"
        return self.client.ensure_org_project(org=org, name=name)

    def link_repo_to_project(
        self,
        org: str,
        repo: str,
        project_id: str,
        *,
        dry_run: bool | None = None,
    ) -> None:
        dr = self._dry_run if dry_run is None else dry_run
        if dr:
            print(f"  [dry-run] link {org}/{repo} → project {project_id}")
            return
        self.client.link_repo_to_project(org=org, repo=repo, project_id=project_id)
