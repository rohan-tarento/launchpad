"""Bootstrap GitHub org: repos + labels from OrgConfig YAML."""

from __future__ import annotations

from pathlib import Path

from launchpad.config import load_gitflow_config, load_org_config, resolve_config_path
from launchpad.github_client import GitHubClient, GitHubError
from launchpad.github_ops import label_exists, repo_access_state


def _repos_for_bootstrap(cfg_path: Path, cfg: dict) -> list[dict]:
    repos = [dict(r) for r in cfg["repos"]]
    seen = {r["name"] for r in repos}
    org = cfg["org"]
    gitflow_path = cfg_path.parent / f"gitflow-{org}.yaml"
    if not gitflow_path.is_file():
        return repos

    gf = load_gitflow_config(gitflow_path)
    app_names = set((gf.get("org_config") or {}).get("repo_names") or [])
    for name in gf.get("repo_names") or []:
        if name in seen:
            continue
        description = f"{name} (tenant meta)" if name not in app_names else name
        repos.append(
            {
                "name": name,
                "private": True,
                "description": description,
            }
        )
        seen.add(name)
    return repos


def run(
    client: GitHubClient,
    org: str = "",
    *,
    config_path: str | None = None,
) -> None:
    cfg_path = resolve_config_path("org", org=org, explicit=config_path)
    cfg = load_org_config(cfg_path)
    org = org or cfg["org"]
    if not org:
        raise ValueError("org is required (config or --org)")

    repos = _repos_for_bootstrap(Path(cfg_path), cfg)

    print(f"=== bootstrap-org (org: {org}) ===")
    print(f"Config: {cfg_path}")
    print(f"Authenticated as: {client.whoami()}")
    print(f"Repos: {len(repos)} (OrgConfig + gitflow union, includes meta)")
    if not client.org_ok(org):
        raise RuntimeError(f"cannot access org {org}")

    repo_states: list[tuple[dict, str]] = []
    for repo in repos:
        name = repo["name"]
        state = repo_access_state(client, org, name)
        repo_states.append((repo, state))
        if state == "exists":
            print(f"Repo exists: {org}/{name}")
        elif state == "forbidden":
            raise RuntimeError(
                f"PAT cannot access {org}/{name} (403). "
                "On your fine-grained PAT set Repository access to "
                "'All repositories' in your org, or explicitly include "
                f"{name}. See playbook/bootstrap-prerequisites.md"
            )
        elif client.dry_run:
            print(f"[dry-run] POST /orgs/{org}/repos name={name}")
            print(
                f"  hint: if {org}/{name} already exists, your PAT likely lacks repository "
                "access (private repos return 404). Use 'All repositories' on the "
                "forge fine-grained token — see playbook/bootstrap-prerequisites.md"
            )
        else:
            print(f"[run] create repo {org}/{name}")
            client.rest(
                "POST",
                f"/orgs/{org}/repos",
                json_body={
                    "name": name,
                    "private": repo.get("private", True),
                    "description": repo.get("description") or f"{name}",
                },
            )
            repo_states[-1] = (repo, "exists")

    for repo, state in repo_states:
        repo_name = repo["name"]
        for label in cfg["labels"]:
            name = label["name"]
            if state == "missing" and client.dry_run:
                print(f"[dry-run] create label {name} on {org}/{repo_name}")
                continue
            if label_exists(client, org, repo_name, name):
                print(f"Label exists: {repo_name} / {name}")
            elif client.dry_run:
                print(f"[dry-run] create label {name} on {org}/{repo_name}")
            else:
                print(f"[run] create label {name} on {org}/{repo_name}")
                try:
                    client.rest(
                        "POST",
                        f"/repos/{org}/{repo_name}/labels",
                        json_body={
                            "name": name,
                            "color": label["color"],
                            "description": label.get("description", name),
                        },
                    )
                except GitHubError as exc:
                    if exc.status == 422 and "already_exists" in (exc.body or ""):
                        print(f"Label exists: {repo_name} / {name}")
                    else:
                        raise

    print("")
    print("=== Done ===")
    if client.dry_run:
        print("Re-run with --apply to execute.")
    print(f"Next: launchpad bootstrap-teams --config {cfg_path} --apply")
