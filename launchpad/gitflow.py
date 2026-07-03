"""Setup gitflow: develop branch, protection, rulesets, optional local templates."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from launchpad.config import load_gitflow_config, tenant_root
from launchpad.paths import resolve_template
from launchpad.gitflow_policy import (
    branch_naming_ref_excludes,
    render_policy_branch_name_workflow,
    render_policy_merge_source_workflow,
)
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


def _ensure_main(
    client: GitHubClient,
    org: str,
    repo: str,
    *,
    init_empty: bool,
    is_meta: bool,
) -> bool:
    if repo_has_main(client, org, repo):
        return True
    if init_empty:
        init_empty_repo_main(client, org, repo)
        return True
    print(f"[skip] {org}/{repo} has no commits on main — cannot create develop yet")
    if is_meta:
        print(
            f"  meta: create github.com/{org}/{repo} if needed, then from local "
            "<client>-meta: git push -u origin main"
        )
    else:
        print(
            f"  app: launchpad scaffold --repo {repo} --apply && git push, "
            "or set options.init_empty: true in gitflow YAML"
        )
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


def _resolve_workspace(options: dict[str, Any]) -> Path:
    raw = str(options.get("workspace") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return tenant_root().parent


def _install_templates_local(
    org: str,
    repo: str,
    profile: str,
    *,
    with_templates: bool,
    workspace: Path,
    branch_naming: dict[str, Any],
    merge_policy: dict[str, Any],
    dry_run: bool,
) -> None:
    if not with_templates:
        return

    dest = workspace / repo
    if not (dest / ".git").is_dir():
        print(f"[skip] templates: no local clone at {dest} (set options.workspace in gitflow YAML)")
        return

    print(f"[templates] {dest} (profile={profile})")
    if dry_run:
        print(f"[dry-run] copy workflows + CODEOWNERS → {dest}")
        return

    codeowners_map = {
        "backend": "CODEOWNERS.backend",
        "frontend": "CODEOWNERS.frontend",
        "platform": "CODEOWNERS.platform",
        "data_platform": "CODEOWNERS.data-platform",
    }
    workflows = dest / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)

    try:
        ci_src = resolve_template("templates/github/workflows/ci.yml")
        co_src = resolve_template(f"templates/{codeowners_map.get(profile, 'CODEOWNERS.platform')}")
        pr_tpl = resolve_template("templates/pull_request_template.md")
    except FileNotFoundError as exc:
        print(f"[skip] templates: {exc}")
        return

    shutil.copy(ci_src, workflows / "ci.yml")
    (workflows / "policy-merge-source.yml").write_text(
        render_policy_merge_source_workflow(merge_policy),
        encoding="utf-8",
    )
    (workflows / "policy-branch-name.yml").write_text(
        render_policy_branch_name_workflow(branch_naming),
        encoding="utf-8",
    )

    co_dest = dest / ".github" / "CODEOWNERS"
    co_dest.parent.mkdir(parents=True, exist_ok=True)
    content = co_src.read_text(encoding="utf-8").replace("@ORG_PLACEHOLDER", f"@{org}")
    co_dest.write_text(content, encoding="utf-8")

    pr_dest = dest / ".github/pull_request_template.md"
    if not pr_dest.is_file():
        shutil.copy(pr_tpl, pr_dest)

    issues_dest = dest / ".github" / "ISSUE_TEMPLATE"
    issues_dest.mkdir(parents=True, exist_ok=True)
    if profile == "platform":
        issue_specs = (
            ("bug.yml", "bug.yml"),
            ("feature.yml", "feature.yml"),
            ("chore.yml", "chore.yml"),
            ("config.yml", "config.yml"),
        )
    else:
        issue_specs = (
            ("bug.app.yml", "bug.yml"),
            ("feature.app.yml", "feature.yml"),
            ("chore.app.yml", "chore.yml"),
            ("config.app.yml", "config.yml"),
        )
    for src_name, dest_name in issue_specs:
        try:
            issue_src = resolve_template(f"templates/issues/{src_name}")
        except FileNotFoundError:
            print(f"[skip] issue template missing: {src_name}")
            continue
        shutil.copy(issue_src, issues_dest / dest_name)

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
    options = cfg["options"]
    branch_naming = cfg["branch_naming"]
    protection = cfg["protection"]
    merge_policy = cfg["merge_policy"]

    require_ci = bool(options.get("require_ci", False))
    apply_naming_ruleset = bool(options.get("branch_naming", False))
    with_templates = bool(options.get("with_templates", False))
    init_empty = bool(options.get("init_empty", False))
    workspace = _resolve_workspace(options)

    print("=== setup-gitflow ===")
    print(f"Org: {org}")
    print(f"Config: {cfg_path}")
    print(f"Authenticated as: {client.whoami()}")
    print(f"options.require_ci: {require_ci}")
    print(f"options.with_templates: {with_templates}")
    print(f"options.init_empty: {init_empty}")
    print(f"options.branch_naming: {apply_naming_ruleset}")
    print(f"branch_naming.mode: {branch_naming.get('mode')}")
    print(f"options.workspace: {workspace}")
    print("")

    if not client.org_ok(org):
        raise RuntimeError(f"cannot access org {org}")

    team_pm = teams.get("pm", "pm-team")
    ref_excludes = branch_naming_ref_excludes(branch_naming)
    app_repos = set((cfg.get("org_config") or {}).get("repo_names") or [])
    skipped: list[tuple[str, str]] = []

    for repo_entry in cfg["repos"]:
        repo = repo_entry["name"]
        profile = repo_entry["profile"]
        is_meta = repo not in app_repos
        if filter_repo and repo != filter_repo:
            continue
        if not repo_exists(client, org, repo):
            print(f"[skip] {org}/{repo} not found on GitHub")
            if is_meta:
                print(
                    "  meta repos are NOT created by bootstrap-org — create the GitHub repo "
                    "and push main from your local <client>-meta clone (docs/new-client.md)"
                )
            else:
                print("  run bootstrap-org --apply first, or create the repo manually")
            skipped.append((repo, "missing"))
            print("")
            continue

        develop_key = repo_entry.get("develop_merge") or profile
        develop_team = team_slug_from_key(teams, develop_key)
        profile_team = team_slug_from_config(teams, profile)

        print(
            f"--- {org}/{repo} (profile={profile}, develop_merge={develop_team}) ---"
        )

        if not _ensure_main(client, org, repo, init_empty=init_empty, is_meta=is_meta):
            skipped.append((repo, "no_main"))
            print("")
            continue

        _ensure_develop(client, org, repo)

        push_teams: list[str] = [team_pm, team_release]
        if develop_key != "pm":
            push_teams.insert(0, profile_team)
        for team_slug in dict.fromkeys(push_teams):
            grant_team_repo_push(client, org, repo, team_slug)

        for push_key in repo_entry.get("grant_push") or []:
            grant_team_repo_push(client, org, repo, team_slug_from_key(teams, push_key))

        for read_key in repo_entry.get("grant_read") or []:
            grant_team_repo_read(client, org, repo, team_slug_from_key(teams, read_key))

        apply_branch_protection(
            client,
            org,
            repo,
            "develop",
            develop_team,
            require_ci=require_ci,
            protection=protection.get("develop"),
        )
        apply_branch_protection(
            client,
            org,
            repo,
            "main",
            team_release,
            require_ci=require_ci,
            protection=protection.get("main"),
        )
        if apply_naming_ruleset:
            apply_branch_naming_ruleset(client, org, repo, ref_excludes=ref_excludes)
        _install_templates_local(
            org,
            repo,
            profile,
            with_templates=with_templates,
            workspace=workspace,
            branch_naming=branch_naming,
            merge_policy=merge_policy,
            dry_run=client.dry_run,
        )
        print("")

    if skipped:
        print("=== Skipped repos (develop not configured) ===")
        for repo, reason in skipped:
            label = "not on GitHub" if reason == "missing" else "no commits on main"
            kind = "meta" if repo not in app_repos else "app"
            print(f"  {org}/{repo} ({kind}): {label}")
        print("")
        print("After all repos have main on GitHub:")
        print(f"  launchpad setup-gitflow --config {cfg_path} --apply")
        print("")

    print("=== Done ===")
    if client.dry_run:
        print("Re-run with --apply to execute.")
    if not require_ci:
        print(
            "Tip: after merging workflow PRs, set options.require_ci: true in gitflow YAML "
            "and re-run setup-gitflow --apply"
        )
    if not with_templates:
        print(
            "Tip: set options.with_templates: true and options.workspace in gitflow YAML "
            "to install workflows into local clones"
        )
