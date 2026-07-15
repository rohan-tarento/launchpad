"""ForgeProvider protocol — abstraction over GitHub (and future providers).

Implementing a new provider (e.g. GitLab in v0.6):
  1. Add providers/gitlab.py implementing ForgeProvider.
  2. Register in providers/__init__.py.
  3. Update programme.yaml schema to accept provider: gitlab.

Every method receives only primitive types (str, dict, bool) so the protocol
is easy to implement and test without heavy fixtures.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ForgeProvider(Protocol):
    """Operations a forge must support for Launchpad to manage a programme."""

    # ── Teams ────────────────────────────────────────────────────────────────

    def ensure_team(
        self,
        org: str,
        name: str,
        *,
        description: str = "",
        privacy: str = "closed",
        dry_run: bool = True,
    ) -> None:
        """Create team if absent.  Idempotent."""
        ...

    # ── Repos ────────────────────────────────────────────────────────────────

    def ensure_repo(
        self,
        org: str,
        name: str,
        *,
        description: str = "",
        visibility: str = "private",
        dry_run: bool = True,
    ) -> None:
        """Create repo if absent.  Idempotent."""
        ...

    def add_team_to_repo(
        self,
        org: str,
        repo: str,
        team: str,
        *,
        permission: str = "push",
        dry_run: bool = True,
    ) -> None:
        """Grant team permission to repo.  Idempotent."""
        ...

    def team_repo_permission(
        self,
        org: str,
        repo: str,
        team: str,
        *,
        dry_run: bool = True,
    ) -> str | None:
        """Return team access to a repository."""
        ...

    def ensure_label(
        self,
        org: str,
        repo: str,
        name: str,
        *,
        color: str,
        description: str = "",
        dry_run: bool = True,
    ) -> None:
        """Create or reconcile a repository label."""
        ...

    # ── Branch protection / gitflow ───────────────────────────────────────────

    def ensure_default_branch(self, org: str, repo: str, branch: str, *, dry_run: bool = True) -> None:
        """Set or verify the default branch."""
        ...

    def ensure_branch(self, org: str, repo: str, branch: str, *, from_branch: str, dry_run: bool = True) -> None:
        """Create branch from from_branch if absent.  Idempotent."""
        ...

    def ensure_branch_protection(
        self,
        org: str,
        repo: str,
        branch: str,
        *,
        required_approvals: int = 1,
        dismiss_stale: bool = True,
        dry_run: bool = True,
    ) -> None:
        """Apply branch protection rules.  Idempotent."""
        ...

    # ── Project board ─────────────────────────────────────────────────────────

    def ensure_project_board(
        self,
        org: str,
        name: str,
        *,
        dry_run: bool = True,
    ) -> str:
        """Create project board if absent; return node_id."""
        ...

    def link_repo_to_project(self, org: str, repo: str, project_id: str, *, dry_run: bool = True) -> None:
        """Link repo to a project board.  Idempotent."""
        ...
