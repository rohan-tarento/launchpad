"""Seed gitflow repos: main, develop, default branch develop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from launchpad.config import load_gitflow_config, resolve_config_path
from launchpad.github_client import GitHubClient
from launchpad.github_ops import (
    create_develop_from_main,
    get_default_branch,
    repo_exists,
    repo_has_main,
    seed_repo_main,
    set_default_branch,
)


class RepoSeedError(RuntimeError):
    """One or more repos could not be seeded."""


def factory_app_repo_names(cfg: dict[str, Any]) -> set[str]:
    org_cfg = cfg.get("org_config") or {}
    return set(org_cfg.get("repo_names") or [])


def seed_one_repo(
    client: GitHubClient,
    org: str,
    repo: str,
    *,
    is_meta: bool,
    seed_empty: bool,
) -> None:
    if not repo_exists(client, org, repo):
        raise RepoSeedError(
            f"{org}/{repo} not found on GitHub — run bootstrap-org (creates all gitflow repos) first"
        )

    if not repo_has_main(client, org, repo):
        if not seed_empty:
            raise RepoSeedError(
                f"{org}/{repo} has no commits on main — set gitflow options.seed_empty: true "
                "or push main before seed-repos"
            )
        seed_repo_main(client, org, repo, is_meta=is_meta)

    create_develop_from_main(client, org, repo)

    current = get_default_branch(client, org, repo)
    if current != "develop":
        set_default_branch(client, org, repo, "develop")
    else:
        print(f"Default branch: {org}/{repo}@develop")


def run(
    client: GitHubClient,
    *,
    org: str = "",
    config_path: Path | str | None = None,
    filter_repo: str = "",
) -> None:
    cfg_path = resolve_config_path("gitflow", org=org, explicit=config_path)
    cfg = load_gitflow_config(cfg_path)
    org = org or cfg["org"]
    options = cfg["options"]
    seed_empty = bool(options.get("seed_empty", True))
    app_repos = factory_app_repo_names(cfg)

    print("=== seed-repos ===")
    print(f"Org: {org}")
    print(f"Config: {cfg_path}")
    print(f"Authenticated as: {client.whoami()}")
    print(f"options.seed_empty: {seed_empty}")
    print("")

    if not client.org_ok(org):
        raise RuntimeError(f"cannot access org {org}")

    errors: list[str] = []
    for repo_entry in cfg["repos"]:
        repo = repo_entry["name"]
        if filter_repo and repo != filter_repo:
            continue
        is_meta = repo not in app_repos
        kind = "meta" if is_meta else "app"
        print(f"--- {org}/{repo} ({kind}) ---")
        try:
            seed_one_repo(
                client,
                org,
                repo,
                is_meta=is_meta,
                seed_empty=seed_empty,
            )
        except RepoSeedError as exc:
            print(f"[FAIL] {exc}")
            errors.append(str(exc))
        except Exception as exc:
            print(f"[FAIL] {org}/{repo}: {exc}")
            errors.append(f"{org}/{repo}: {exc}")
        print("")

    if errors:
        print("=== seed-repos: FAILED ===")
        raise RepoSeedError(
            f"{len(errors)} repo(s) not seeded — fix errors above and re-run seed-repos --apply"
        )

    print("=== Done ===")
    if client.dry_run:
        print("Re-run with --apply to execute.")
    print(f"Next: launchpad setup-gitflow --config {cfg_path} --apply")
