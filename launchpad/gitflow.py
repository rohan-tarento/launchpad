"""Setup gitflow: develop branch, protection, rulesets, optional local templates."""

from __future__ import annotations

import shutil
from pathlib import Path

from launchpad.config import load_gitflow_config, tenant_root
from launchpad.github_client import GitHubClient
from launchpad.github_ops import (
    apply_branch_naming_ruleset,
    apply_branch_protection,
    branch_exists,
    grant_team_repo_push,
    grant_team_repo_read,
    init_empty_repo_main,
    main_sha,
    repo_exists,
    repo_has_main,
    team_slug_from_config,
    team_slug_from_key,
)


def _ensure_main(client: GitHubClient, org: str, repo: str, *, init_empty: bool) -> bool:
    if repo_has_main(client, org, repo):
        return True
    if init_empty:
        init_empty_repo_main(client, org, repo)
        return True
    print(f"[skip] {org}/{repo} has no commits on main — push content or use --init-empty")
    return False


def _ensure_develop(client: GitHubClient, org: str, repo: str) -> None:
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


def _install_templates_local(
    org: str,
    repo: str,
    profile: str,
    *,
    with_templates: bool,
    workspace: Path | None,
    dry_run: bool,
) -> None:
    if not with_templates:
        return

    root = tenant_root()
    ws = workspace or (root.parent)
    dest = ws / repo
    if not (dest / ".git").is_dir():
        print(f"[skip] templates: no local clone at {dest} (use --workspace)")
        return

    print(f"[templates] {dest} (profile={profile})")
    if dry_run:
        print(f"[dry-run] copy workflows + CODEOWNERS → {dest}")
        return

    workflows = dest / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)

    shutil.copy(root / "templates/github/workflows/ci.yml", workflows / "ci.yml")
    shutil.copy(
        root / "templates/github/workflows/policy-merge-source.yml",
        workflows / "policy-merge-source.yml",
    )
    shutil.copy(
        root / "templates/github/workflows/policy-branch-name.yml",
        workflows / "policy-branch-name.yml",
    )

    codeowners_map = {
        "backend": "CODEOWNERS.backend",
        "frontend": "CODEOWNERS.frontend",
        "platform": "CODEOWNERS.platform",
        "data_platform": "CODEOWNERS.data-platform",
    }
    co_src = root / "templates" / codeowners_map.get(profile, "CODEOWNERS.platform")
    co_dest = dest / ".github" / "CODEOWNERS"
    co_dest.parent.mkdir(parents=True, exist_ok=True)
    content = co_src.read_text(encoding="utf-8").replace("@ORG_PLACEHOLDER", f"@{org}")
    co_dest.write_text(content, encoding="utf-8")

    pr_tpl = root / "templates/pull_request_template.md"
    pr_dest = dest / ".github/pull_request_template.md"
    if pr_tpl.is_file() and not pr_dest.is_file():
        shutil.copy(pr_tpl, pr_dest)

    print("  → committed locally; open PR: chore/setup-gitflow-enforcement")
    print(
        f"  → cd {dest} && git checkout -b chore/setup-gitflow-enforcement "
        "&& git add .github && git commit -m 'chore: add gitflow enforcement workflows'"
    )


def run(
    client: GitHubClient,
    *,
    org: str = "",
    config_path: Path | str | None = None,
    filter_repo: str = "",
    workspace: Path | str | None = None,
    with_templates: bool | None = None,
    init_empty: bool | None = None,
    require_ci: bool | None = None,
    branch_naming: bool | None = None,
) -> None:
    from launchpad.config import resolve_config_path

    cfg_path = resolve_config_path(
        "gitflow",
        org=org,
        explicit=config_path,
    )
    cfg = load_gitflow_config(cfg_path)
    org = org or cfg["org"]
    teams: dict[str, str] = cfg["teams"]
    team_release = teams.get("release_managers", "release-managers")
    opts = cfg.get("options") or {}
    require_ci = bool(opts.get("require_ci", False)) if require_ci is None else require_ci
    branch_naming = bool(opts.get("branch_naming", False)) if branch_naming is None else branch_naming
    with_templates = bool(opts.get("with_templates", False)) if with_templates is None else with_templates
    init_empty = bool(opts.get("init_empty", False)) if init_empty is None else init_empty

    print("=== setup-gitflow ===")
    print(f"Org: {org}")
    print(f"Config: {cfg_path}")
    print(f"Authenticated as: {client.whoami()}")
    print(f"require-ci: {require_ci}")
    print(f"with-templates: {with_templates}")
    print(f"init-empty: {init_empty}")
    print(f"branch-naming: {branch_naming}")
    print("")

    if not client.org_ok(org):
        raise RuntimeError(f"cannot access org {org}")

    ws_path = Path(workspace) if workspace else None

    team_pm = teams.get("pm", "pm-team")

    for repo_entry in cfg["repos"]:
        repo = repo_entry["name"]
        profile = repo_entry["profile"]
        if filter_repo and repo != filter_repo:
            continue
        if not repo_exists(client, org, repo):
            print(f"[skip] repo not found: {org}/{repo}")
            continue

        develop_key = repo_entry.get("develop_merge") or profile
        develop_team = team_slug_from_key(teams, develop_key)
        profile_team = team_slug_from_config(teams, profile)

        print(
            f"--- {org}/{repo} (profile={profile}, develop_merge={develop_team}) ---"
        )

        if not _ensure_main(client, org, repo, init_empty=init_empty):
            print("")
            continue

        _ensure_develop(client, org, repo)

        # Push: PM on all repos; profile dev team on app repos; meta = PM only (+ release)
        push_teams: list[str] = [team_pm, team_release]
        if develop_key != "pm":
            push_teams.insert(0, profile_team)
        for team_slug in dict.fromkeys(push_teams):
            grant_team_repo_push(client, org, repo, team_slug)

        # Read on meta for dev teams (PRD access without write)
        for read_key in repo_entry.get("grant_read") or []:
            grant_team_repo_read(client, org, repo, team_slug_from_key(teams, read_key))

        apply_branch_protection(
            client, org, repo, "develop", develop_team, require_ci=require_ci
        )
        apply_branch_protection(
            client, org, repo, "main", team_release, require_ci=require_ci
        )
        if branch_naming:
            apply_branch_naming_ruleset(client, org, repo)
        _install_templates_local(
            org,
            repo,
            profile,
            with_templates=with_templates,
            workspace=ws_path,
            dry_run=client.dry_run,
        )
        print("")

    print("=== Done ===")
    if client.dry_run:
        print("Re-run with --apply to execute.")
    if not require_ci:
        print("Tip: after merging workflow PRs, re-run with --require-ci")
    if not with_templates:
        print("Tip: use --with-templates --workspace <parent-of-clones> to install workflows locally")
