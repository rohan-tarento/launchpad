"""Platform verify check handlers keyed by VerifyManifest check id."""

from __future__ import annotations

from typing import Any, Callable

from launchpad.github_client import GitHubClient, GitHubError
from launchpad.github_ops import branch_exists, label_exists, repo_exists, team_exists
from launchpad.issue_types import ISSUE_TYPES_PAT_HINT, list_org_issue_types, verify_issue_types_scope
from launchpad.project import _project_meta, _project_number_by_title, verify_project_scope

CheckResult = tuple[bool, str]
CheckFn = Callable[[GitHubClient, str, dict[str, Any], dict[str, Any]], CheckResult]
CHECKS: dict[str, CheckFn] = {}


def _register(check_id: str) -> Callable[[CheckFn], CheckFn]:
    def deco(fn: CheckFn) -> CheckFn:
        CHECKS[check_id] = fn
        return fn

    return deco


def _repo_list(ctx: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    key = str(spec.get("repos_from", ""))
    if key == "org.repos":
        org_cfg = ctx.get("org_config") or {}
        return list(org_cfg.get("repo_names") or [])
    if key == "gitflow.repos":
        gitflow = ctx.get("gitflow") or {}
        return list(gitflow.get("repo_names") or [])
    return []


@_register("org.access")
def check_org_access(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    _ = ctx, spec
    ok = client.org_ok(org)
    return ok, "" if ok else "token cannot access org"


@_register("projects.api")
def check_projects_api(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    _ = ctx, spec
    try:
        verify_project_scope(client, org)
        return True, ""
    except RuntimeError as exc:
        return False, str(exc)


@_register("issue_types.api")
def check_issue_types_api(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    _ = spec
    try:
        verify_issue_types_scope(client, org)
        return True, ""
    except RuntimeError as exc:
        return False, f"{exc} {ISSUE_TYPES_PAT_HINT}"


@_register("repos.present")
def check_repos_present(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    missing = [r for r in _repo_list(ctx, spec) if not repo_exists(client, org, r)]
    if missing:
        return False, f"missing repos: {missing}"
    return True, f"{len(_repo_list(ctx, spec))} repos"


@_register("labels.present")
def check_labels_present(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    org_cfg = ctx.get("org_config") or {}
    labels = org_cfg.get("labels") or []
    repos = org_cfg.get("repo_names") or []
    if not repos or not labels:
        return False, "no labels or repos in org config"
    sample_repo = repos[0]
    missing = [lb["name"] for lb in labels if not label_exists(client, org, sample_repo, lb["name"])]
    if missing:
        return False, f"missing on {sample_repo}: {missing[:5]}"
    return True, f"{len(labels)} labels on {sample_repo}"


@_register("teams.present")
def check_teams_present(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    org_cfg = ctx.get("org_config") or {}
    teams = org_cfg.get("teams") or []
    missing = [t["slug"] for t in teams if not team_exists(client, org, t["slug"])]
    if missing:
        return False, f"missing teams: {missing}"
    return True, f"{len(teams)} teams"


@_register("gitflow.develop")
def check_gitflow_develop(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    missing = [r for r in _repo_list(ctx, spec) if not branch_exists(client, org, r, "develop")]
    if missing:
        return False, f"no develop branch: {missing}"
    return True, f"develop on {len(_repo_list(ctx, spec))} repos"


@_register("gitflow.protection")
def check_gitflow_protection(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    failed: list[str] = []
    for repo in _repo_list(ctx, spec):
        for branch in ("main", "develop"):
            try:
                client.rest("GET", f"/repos/{org}/{repo}/branches/{branch}/protection")
            except GitHubError:
                failed.append(f"{repo}@{branch}")
            except Exception:
                failed.append(f"{repo}@{branch}")
    if failed:
        return False, f"no protection: {failed}"
    return True, "main + develop protected"


@_register("project.present")
def check_project_present(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    project = ctx.get("project") or {}
    title = project.get("project_title", "")
    if not title:
        return False, "project_title missing in config"
    num = _project_number_by_title(client, org, title)
    if num is None:
        return False, f"project {title!r} not found"
    return True, f"{title} (#{num})"


@_register("project.repos_linked")
def check_project_repos_linked(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    project = ctx.get("project") or {}
    title = project.get("project_title", "")
    repos = _repo_list(ctx, spec)
    num = _project_number_by_title(client, org, title)
    if num is None:
        return False, "project not found"
    meta = _project_meta(client, org, num)
    project_id = meta["id"]
    data = client.graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on ProjectV2 {
              repositories(first: 50) { nodes { name } }
            }
          }
        }
        """,
        {"id": project_id},
    )
    linked = {
        n.get("name")
        for n in (data.get("node") or {}).get("repositories", {}).get("nodes") or []
        if n.get("name")
    }
    missing = [r for r in repos if r not in linked]
    if missing:
        return False, f"not linked to project: {missing}"
    return True, f"{len(repos)} repos linked"


@_register("issue_types.present")
def check_issue_types_present(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    project = ctx.get("project") or {}
    ensure = project.get("issue_types_ensure") or []
    names = [str(n.get("name", "")) for n in ensure if isinstance(n, dict)]
    names = [n for n in names if n]
    existing = list_org_issue_types(client, org)
    missing = [n for n in names if n not in existing]
    if missing:
        return False, f"missing types: {missing}"
    return True, ", ".join(names)


@_register("config.repos_aligned")
def check_config_repos_aligned(client: GitHubClient, org: str, ctx: dict, spec: dict) -> CheckResult:
    _ = client, org, spec
    org_cfg = ctx.get("org_config") or {}
    gitflow = ctx.get("gitflow") or {}
    project = ctx.get("project") or {}
    org_repos = set(org_cfg.get("repo_names") or [])
    gitflow_repos = set(gitflow.get("repo_names") or [])
    project_repos = set(project.get("repos") or [])
    if not org_repos:
        return False, "org.repos empty"
    if gitflow_repos and gitflow_repos != org_repos:
        return False, f"gitflow repos mismatch: {sorted(gitflow_repos ^ org_repos)}"
    if project_repos and project_repos != org_repos:
        return False, f"project repos mismatch: {sorted(project_repos ^ org_repos)}"
    return True, "org = gitflow = project"
