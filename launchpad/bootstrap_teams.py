"""Create engineering teams from OrgConfig YAML."""

from __future__ import annotations

from launchpad.config import load_org_config, resolve_config_path
from launchpad.github_client import GitHubClient
from launchpad.github_ops import team_exists


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

    print(f"=== bootstrap-teams (org: {org}) ===")
    print(f"Config: {cfg_path}")
    print(f"Authenticated as: {client.whoami()}")
    if not client.org_ok(org):
        raise RuntimeError(f"cannot access org {org}")

    for team in cfg["teams"]:
        slug = team["slug"]
        description = team.get("description", "")
        privacy = team.get("privacy", "closed")
        if team_exists(client, org, slug):
            print(f"Team exists: {slug}")
        else:
            if client.dry_run:
                print(
                    f"[dry-run] POST orgs/{org}/teams name={slug} "
                    f"description={description!r} privacy={privacy}"
                )
            else:
                print(f"[run] create team {slug}")
                client.rest(
                    "POST",
                    f"/orgs/{org}/teams",
                    json_body={
                        "name": slug,
                        "description": description,
                        "privacy": privacy,
                    },
                )

    print("")
    print("=== Done ===")
    print(f"Add members: https://github.com/orgs/{org}/teams")
    if client.dry_run:
        print("Re-run with --apply to create missing teams.")
