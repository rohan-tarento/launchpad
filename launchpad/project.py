"""GitHub Projects v2 bootstrap (GraphQL)."""

from __future__ import annotations

from typing import Any

from launchpad.config import discover_tenant_config, load_project_config, tenant_root
from launchpad.github_client import GitHubClient, GitHubError
from launchpad.github_ops import repo_exists
from launchpad.issue_types import ensure_org_issue_types

STATUS_COLORS = ["GRAY", "BLUE", "GREEN", "YELLOW", "ORANGE", "RED", "PURPLE"]


def _org_node_id(client: GitHubClient, org: str) -> str:
    data = client.graphql(
        """
        query($login: String!) {
          organization(login: $login) { id }
        }
        """,
        {"login": org},
    )
    node_id = data.get("organization", {}).get("id")
    if not node_id:
        raise GitHubError(f"organization not found: {org}")
    return node_id


def _project_number_by_title(client: GitHubClient, org: str, title: str) -> int | None:
    data = client.graphql(
        """
        query($login: String!, $title: String!) {
          organization(login: $login) {
            projectsV2(first: 50, query: $title) {
              nodes { number title }
            }
          }
        }
        """,
        {"login": org, "title": title},
    )
    for node in data.get("organization", {}).get("projectsV2", {}).get("nodes") or []:
        if node.get("title") == title:
            return int(node["number"])
    return None


def _project_meta(client: GitHubClient, org: str, number: int) -> dict[str, Any]:
    data = client.graphql(
        """
        query($login: String!, $number: Int!) {
          organization(login: $login) {
            projectV2(number: $number) { id title url }
          }
        }
        """,
        {"login": org, "number": number},
    )
    proj = data.get("organization", {}).get("projectV2")
    if not proj:
        raise GitHubError(f"project #{number} not found in {org}")
    return proj


def _single_select_field(client: GitHubClient, project_id: str, name: str) -> dict[str, Any]:
    data = client.graphql(
        """
        query($id: ID!, $name: String!) {
          node(id: $id) {
            ... on ProjectV2 {
              field(name: $name) {
                ... on ProjectV2SingleSelectField {
                  id
                  options { id name }
                }
              }
            }
          }
        }
        """,
        {"id": project_id, "name": name},
    )
    return (data.get("node") or {}).get("field") or {}


def _status_field(client: GitHubClient, project_id: str) -> dict[str, Any]:
    return _single_select_field(client, project_id, "Status")


def _status_options_mutation(desired: list[str], current: dict[str, Any]) -> list[dict[str, Any]]:
    opts = {o["name"]: o["id"] for o in (current.get("options") or [])}
    out: list[dict[str, Any]] = []
    for i, name in enumerate(desired):
        entry: dict[str, Any] = {
            "name": name,
            "color": STATUS_COLORS[i % len(STATUS_COLORS)],
            "description": name,
        }
        if name in opts:
            entry["id"] = opts[name]
        out.append(entry)
    return out


def _field_names(client: GitHubClient, project_id: str) -> set[str]:
    data = client.graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on ProjectV2 {
              fields(first: 50) {
                nodes { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
        }
        """,
        {"id": project_id},
    )
    nodes = (data.get("node") or {}).get("fields", {}).get("nodes") or []
    return {n.get("name") for n in nodes if n.get("name")}


def _repo_node_id(client: GitHubClient, org: str, repo: str) -> str:
    data = client.graphql(
        """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) { id }
        }
        """,
        {"owner": org, "name": repo},
    )
    node_id = (data.get("repository") or {}).get("id")
    if not node_id:
        raise GitHubError(f"repository not found: {org}/{repo}")
    return node_id


def ensure_project(client: GitHubClient, org: str, title: str) -> int:
    num = _project_number_by_title(client, org, title)
    if num is not None:
        print(f"Project exists: {org} / {title} (#{num})")
        return num
    if client.dry_run:
        print(f"[dry-run] create project: {title}")
        return 0
    org_id = _org_node_id(client, org)
    print(f"[run] create project: {title}")
    data = client.graphql(
        """
        mutation($ownerId: ID!, $title: String!) {
          createProjectV2(input: {ownerId: $ownerId, title: $title}) {
            projectV2 { number }
          }
        }
        """,
        {"ownerId": org_id, "title": title},
    )
    return int(data["createProjectV2"]["projectV2"]["number"])


def _apply_single_select_options(
    client: GitHubClient,
    project_id: str,
    field_name: str,
    desired: list[str],
) -> None:
    current = _single_select_field(client, project_id, field_name)
    field_id = current.get("id")
    if not field_id:
        raise GitHubError(f"{field_name} field not found on project")

    options = _status_options_mutation(desired, current)
    label = ", ".join(desired)
    if client.dry_run:
        print(f"[dry-run] updateProjectV2Field {field_name} → {label}")
        return
    print(f"[run] update {field_name} options: {label}")
    client.graphql(
        """
        mutation($fieldId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
          updateProjectV2Field(input: {fieldId: $fieldId, singleSelectOptions: $options}) {
            projectV2Field { ... on ProjectV2SingleSelectField { id name } }
          }
        }
        """,
        {"fieldId": field_id, "options": options},
    )


def apply_status_columns(client: GitHubClient, project_id: str, columns: list[str]) -> None:
    _apply_single_select_options(client, project_id, "Status", columns)


def ensure_custom_field(
    client: GitHubClient,
    project_id: str,
    name: str,
    field_type: str,
    options: list[str],
) -> None:
    if client.dry_run:
        if field_type == "SINGLE_SELECT":
            print(f"[dry-run] ensure field: {name} ({field_type}) → {', '.join(options)}")
        else:
            print(f"[dry-run] create field: {name} ({field_type})")
        return

    if name in _field_names(client, project_id):
        if field_type == "SINGLE_SELECT":
            _apply_single_select_options(client, project_id, name, options)
        else:
            print(f"Field exists: {name}")
        return

    print(f"[run] create field: {name} ({field_type})")
    if field_type == "TEXT":
        client.graphql(
            """
            mutation($projectId: ID!, $name: String!) {
              createProjectV2Field(input: {
                projectId: $projectId
                dataType: TEXT
                name: $name
              }) {
                projectV2Field { ... on ProjectV2FieldCommon { id name } }
              }
            }
            """,
            {"projectId": project_id, "name": name},
        )
    elif field_type == "SINGLE_SELECT":
        select_opts = [
            {
                "name": str(opt),
                "color": STATUS_COLORS[i % len(STATUS_COLORS)],
                "description": str(opt),
            }
            for i, opt in enumerate(options)
        ]
        client.graphql(
            """
            mutation($projectId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
              createProjectV2Field(input: {
                projectId: $projectId
                dataType: SINGLE_SELECT
                name: $name
                singleSelectOptions: $options
              }) {
                projectV2Field { ... on ProjectV2FieldCommon { id name } }
              }
            }
            """,
            {"projectId": project_id, "name": name, "options": select_opts},
        )
    else:
        raise ValueError(f"unsupported field type: {field_type}")


def link_repo_to_project(client: GitHubClient, org: str, project_id: str, repo: str) -> None:
    if client.dry_run:
        print(f"[dry-run] link project → {org}/{repo}")
        return
    if not repo_exists(client, org, repo):
        print(f"[skip] repo not found: {org}/{repo}")
        return
    print(f"[run] link repo: {org}/{repo}")
    repo_id = _repo_node_id(client, org, repo)
    try:
        client.graphql(
            """
            mutation($projectId: ID!, $repositoryId: ID!) {
              linkProjectV2ToRepository(input: {
                projectId: $projectId
                repositoryId: $repositoryId
              }) {
                repository { name }
              }
            }
            """,
            {"projectId": project_id, "repositoryId": repo_id},
        )
    except GitHubError as exc:
        if "already" in str(exc.body).lower():
            print("  (already linked)")
        else:
            print("  (already linked or link skipped)")


def verify_project_scope(client: GitHubClient, org: str) -> None:
    """Fail fast if token lacks project read scope."""
    if client.dry_run and client.token == "dry-run":
        return
    try:
        _project_number_by_title(client, org, "__meta_scope_probe__")
    except GitHubError as exc:
        if exc.status in (401, 403):
            raise RuntimeError(
                "GitHub token lacks project scope. Fine-grained PAT needs "
                "Projects: Read and write. Classic PAT: read:project + project."
            ) from exc
        raise


def run(
    client: GitHubClient,
    *,
    org: str = "",
    config_path: str | None = None,
) -> None:
    cfg_path = config_path or str(discover_tenant_config("project", org=org or ""))
    cfg = load_project_config(cfg_path)
    org = org or cfg["org"]
    title = cfg["project_title"]

    print("=== bootstrap-project ===")
    print(f"Org: {org}")
    print(f"Config: {cfg_path}")
    print(f"Project: {title}")
    print(f"Authenticated as: {client.whoami()}")
    print("")

    if not client.org_ok(org):
        raise RuntimeError(f"cannot access org {org}")
    verify_project_scope(client, org)

    if cfg["issue_types_required"] and not cfg["issue_types_ensure"]:
        raise RuntimeError(
            "project config issue_types.required is true but issue_types.ensure is empty"
        )
    if cfg["issue_types_ensure"]:
        label = "required" if cfg["issue_types_required"] else "optional"
        print(f"Issue types (org) — {label} by project config:")
        ensure_org_issue_types(client, org, cfg["issue_types_ensure"])
        if cfg["issue_types_required"] and not client.dry_run:
            names = ", ".join(s["name"] for s in cfg["issue_types_ensure"])
            print(f"  verified: {names}")
        print("")

    project_num = ensure_project(client, org, title)

    if project_num == 0 and client.dry_run:
        print("[dry-run] would configure Status + fields + repo links")
        if cfg["issue_type_roles"]:
            print(f"[dry-run] issue type roles: {cfg['issue_type_roles']}")
        for field in cfg["fields"]:
            ensure_custom_field(
                client,
                "PVT_dryrun",
                field["name"],
                field["type"],
                field["options"],
            )
        for repo in cfg["repos"]:
            link_repo_to_project(client, org, "PVT_dryrun", repo)
        print("")
        print("=== Done (dry-run) ===")
        return

    meta = _project_meta(client, org, project_num)
    project_id = meta["id"]
    project_url = meta["url"]

    apply_status_columns(client, project_id, cfg["status_columns"])

    for field in cfg["fields"]:
        ensure_custom_field(
            client,
            project_id,
            field["name"],
            field["type"],
            field["options"],
        )

    for repo in cfg["repos"]:
        link_repo_to_project(client, org, project_id, repo)

    print("")
    print("=== Done ===")
    print(f"Project: {project_url}")
    print("Record this URL in playbook/github-org-setup.md or README.md")
    if client.dry_run:
        print("Re-run with --apply to execute.")
