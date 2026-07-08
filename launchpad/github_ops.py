"""High-level GitHub REST helpers used by bootstrap modules."""

from __future__ import annotations

import base64
from typing import Any

from launchpad.github_client import GitHubClient, GitHubError, GitHubError

BRANCH_NAME_REF_EXCLUDES = [
    "refs/heads/main",
    "refs/heads/develop",
    "refs/heads/feature/**",
    "refs/heads/fix/**",
    "refs/heads/hotfix/**",
    "refs/heads/release/**",
    "refs/heads/chore/**",
    "refs/heads/dependabot/**",
]


def repo_access_state(client: GitHubClient, org: str, repo: str) -> str:
    """Return exists | missing | forbidden for a repo GET."""
    try:
        client.rest("GET", f"/repos/{org}/{repo}")
        return "exists"
    except GitHubError as exc:
        if exc.status == 404:
            return "missing"
        if exc.status == 403:
            return "forbidden"
        raise


def repo_exists(client: GitHubClient, org: str, repo: str) -> bool:
    return repo_access_state(client, org, repo) == "exists"


def branch_exists(client: GitHubClient, org: str, repo: str, branch: str) -> bool:
    try:
        client.rest("GET", f"/repos/{org}/{repo}/branches/{branch}")
        return True
    except Exception:
        return False


def main_sha(client: GitHubClient, org: str, repo: str) -> str:
    ref = client.rest("GET", f"/repos/{org}/{repo}/git/ref/heads/main")
    return ref["object"]["sha"]


def repo_has_main(client: GitHubClient, org: str, repo: str) -> bool:
    try:
        main_sha(client, org, repo)
        return True
    except Exception:
        return False


def label_exists(client: GitHubClient, org: str, repo: str, name: str) -> bool:
    page = 1
    while True:
        try:
            labels = client.rest(
                "GET",
                f"/repos/{org}/{repo}/labels",
                params={"per_page": 100, "page": page},
            )
        except GitHubError as exc:
            if exc.status in (403, 404):
                return False
            raise
        if not isinstance(labels, list) or not labels:
            return False
        if any(lb.get("name") == name for lb in labels):
            return True
        if len(labels) < 100:
            return False
        page += 1


def team_exists(client: GitHubClient, org: str, slug: str) -> bool:
    try:
        client.rest("GET", f"/orgs/{org}/teams/{slug}")
        return True
    except Exception:
        return False


def seed_repo_main(client: GitHubClient, org: str, repo: str, *, is_meta: bool = False) -> None:
    if is_meta:
        content = (
            f"# {repo}\n\n"
            "Tenant meta seeded by launchpad setup-platform.\n"
            "PM: open a chore PR to develop with prd/, work/, and config/ content.\n"
        )
    else:
        content = (
            f"# {repo}\n\n"
            "Seeded by launchpad setup-platform.\n"
            "Replace via scaffold + PR to develop.\n"
        )
    b64 = base64.b64encode(content.encode()).decode()
    if client.dry_run:
        print(f"[dry-run] PUT repos/{org}/{repo}/contents/README.md (initial commit on main)")
        return
    print(f"[run] seed main: {org}/{repo}")
    client.rest(
        "PUT",
        f"/repos/{org}/{repo}/contents/README.md",
        json_body={
            "message": "chore: seed repo (setup-platform)",
            "content": b64,
        },
    )


def init_empty_repo_main(client: GitHubClient, org: str, repo: str) -> None:
    """Backward-compatible alias for seed_repo_main."""
    seed_repo_main(client, org, repo, is_meta=False)


def get_default_branch(client: GitHubClient, org: str, repo: str) -> str:
    if client.dry_run and not repo_exists(client, org, repo):
        return "main"
    data = client.rest("GET", f"/repos/{org}/{repo}")
    return str(data.get("default_branch") or "main")


def _github_error_detail(exc: GitHubError) -> str:
    import json

    if not exc.body:
        return str(exc)
    try:
        data = json.loads(exc.body)
    except json.JSONDecodeError:
        return exc.body[:300]
    errors = data.get("errors") or []
    if errors and isinstance(errors[0], dict):
        msg = errors[0].get("message")
        if msg:
            return str(msg)
    message = data.get("message")
    return str(message) if message else exc.body[:300]


def set_default_branch(client: GitHubClient, org: str, repo: str, branch: str) -> None:
    if client.dry_run:
        print(f"[dry-run] PATCH repos/{org}/{repo} default_branch={branch}")
        return
    print(f"[run] default branch → {branch}: {org}/{repo}")
    try:
        client.rest(
            "PATCH",
            f"/repos/{org}/{repo}",
            json_body={"default_branch": branch},
        )
    except GitHubError as exc:
        detail = _github_error_detail(exc)
        hint = ""
        if "permission to change the default branch" in detail.lower():
            hint = (
                " — org policy blocks non-owners; ask an org owner to set default branch "
                "to develop in GitHub UI, or set gitflow options.set_default_branch: false"
            )
        raise GitHubError(
            f"PATCH /repos/{org}/{repo} default_branch={branch} failed: {detail}{hint}",
            exc.status,
            exc.body,
        ) from exc


def create_develop_from_main(client: GitHubClient, org: str, repo: str) -> None:
    if branch_exists(client, org, repo, "develop"):
        print(f"Branch exists: {org}/{repo}@develop")
        return
    if client.dry_run and not repo_has_main(client, org, repo):
        print(f"[dry-run] create refs/heads/develop from main on {org}/{repo}")
        return
    sha = main_sha(client, org, repo)
    if client.dry_run:
        print(f"[dry-run] create refs/heads/develop @ {sha[:7]} on {org}/{repo}")
        return
    print(f"[run] create develop from main on {org}/{repo}")
    client.rest(
        "POST",
        f"/repos/{org}/{repo}/git/refs",
        json_body={"ref": "refs/heads/develop", "sha": sha},
    )


def grant_team_repo_permission(
    client: GitHubClient,
    org: str,
    repo: str,
    team_slug: str,
    permission: str,
) -> None:
    if client.dry_run:
        print(f"[dry-run] grant team {team_slug} {permission} on {org}/{repo}")
        return
    print(f"[run] grant team {team_slug} {permission} on {org}/{repo}")
    client.rest(
        "PUT",
        f"/orgs/{org}/teams/{team_slug}/repos/{org}/{repo}",
        json_body={"permission": permission},
    )


def grant_team_repo_push(client: GitHubClient, org: str, repo: str, team_slug: str) -> None:
    grant_team_repo_permission(client, org, repo, team_slug, "push")


def grant_team_repo_read(client: GitHubClient, org: str, repo: str, team_slug: str) -> None:
    grant_team_repo_permission(client, org, repo, team_slug, "pull")


def team_slug_from_config(teams: dict[str, str], profile: str) -> str:
    profile_key = {
        "backend": "backend",
        "frontend": "frontend",
        "platform": "platform",
        "data_platform": "data_platform",
        "pm": "pm",
    }.get(profile)
    if not profile_key:
        raise ValueError(f"unknown profile: {profile}")
    slug = teams.get(profile_key)
    if not slug:
        raise ValueError(f"no team slug for profile {profile}")
    return slug


def team_slug_from_key(teams: dict[str, str], key: str) -> str:
    if key in teams:
        return teams[key]
    return team_slug_from_config(teams, key)


def apply_branch_protection(
    client: GitHubClient,
    org: str,
    repo: str,
    branch: str,
    team_slug: str,
    *,
    require_ci: bool,
    protection: dict[str, Any] | None = None,
) -> None:
    prot = protection or {}
    checks: dict[str, Any] | None = None
    if require_ci:
        if branch == "main":
            checks = {
                "strict": True,
                "checks": [{"context": "ci"}, {"context": "policy-merge-source"}],
            }
        else:
            checks = {
                "strict": True,
                "checks": [{"context": "ci"}, {"context": "policy-branch-name"}],
            }

    payload: dict[str, Any] = {
        "required_status_checks": checks,
        "enforce_admins": bool(prot.get("enforce_admins", True)),
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": bool(prot.get("dismiss_stale_reviews", True)),
            "require_code_owner_reviews": bool(prot.get("require_code_owner_reviews", False)),
            "required_approving_review_count": int(
                prot.get("required_approving_review_count", 1)
            ),
        },
        "restrictions": {"users": [], "teams": [team_slug], "apps": []},
        "required_linear_history": False,
        "allow_force_pushes": bool(prot.get("allow_force_pushes", False)),
        "allow_deletions": bool(prot.get("allow_deletions", False)),
        "block_creations": False,
    }

    if client.dry_run:
        print(
            f"[dry-run] PUT repos/{org}/{repo}/branches/{branch}/protection "
            f"(team={team_slug}, checks={require_ci})"
        )
        return

    print(f"[run] branch protection: {org}/{repo}@{branch} → team {team_slug}")
    client.rest(
        "PUT",
        f"/repos/{org}/{repo}/branches/{branch}/protection",
        json_body=payload,
    )


def apply_branch_naming_ruleset(
    client: GitHubClient,
    org: str,
    repo: str,
    *,
    ref_excludes: list[str] | None = None,
) -> None:
    ruleset_name = "branch-naming-standard"
    existing_id: int | None = None
    try:
        rulesets = client.rest("GET", f"/repos/{org}/{repo}/rulesets")
        if isinstance(rulesets, list):
            for rs in rulesets:
                if rs.get("name") == ruleset_name:
                    existing_id = rs.get("id")
                    break
    except Exception:
        pass

    excludes = ref_excludes if ref_excludes is not None else BRANCH_NAME_REF_EXCLUDES
    payload = {
        "name": ruleset_name,
        "target": "branch",
        "enforcement": "active",
        "conditions": {
            "ref_name": {
                "include": ["~ALL"],
                "exclude": excludes,
            }
        },
        "rules": [
            {"type": "creation"},
            {"type": "update", "parameters": {"update_allows_fetch_and_merge": True}},
        ],
    }

    if client.dry_run:
        action = "UPDATE" if existing_id else "POST"
        print(f"[dry-run] {action} repos/{org}/{repo}/rulesets (branch naming)")
        return

    if existing_id:
        print(f"[run] update branch naming ruleset on {org}/{repo}")
        client.rest("PUT", f"/repos/{org}/{repo}/rulesets/{existing_id}", json_body=payload)
    else:
        print(f"[run] create branch naming ruleset on {org}/{repo}")
        client.rest("POST", f"/repos/{org}/{repo}/rulesets", json_body=payload)
