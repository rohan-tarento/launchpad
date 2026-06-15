"""Seed GitHub issues + Project items from a WorkManifest YAML."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from launchpad.config import (
    coerce_yaml_select_option,
    default_project_config_path,
    load_project_config,
    load_work_manifest,
    tenant_root,
)
from launchpad.github_client import GitHubClient, GitHubError
from launchpad.config import default_verify_config_path
from launchpad.issue_types import resolve_issue_type_name
from launchpad.verify.runner import VerifyError, run_applied
from launchpad.project import (
    _project_meta,
    _project_number_by_title,
    verify_project_scope,
)

# WorkManifest keys → GitHub Project v2 custom field display names
_FIELD_MAP = {
    "initiative": "Initiative",
    "cr": "CR",
    "codebase": "Codebase",
    "spec_path": "Spec path",
    "verify_command": "Verify command",
    "as_built": "As-built",
    "qa_manifest": "QA manifest",
    "status": "Status",
}


def _project_fields(client: GitHubClient, project_id: str) -> dict[str, dict[str, Any]]:
    data = client.graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on ProjectV2 {
              fields(first: 50) {
                nodes {
                  ... on ProjectV2FieldCommon { id name dataType }
                  ... on ProjectV2SingleSelectField {
                    id name dataType
                    options { id name }
                  }
                }
              }
            }
          }
        }
        """,
        {"id": project_id},
    )
    out: dict[str, dict[str, Any]] = {}
    nodes = (data.get("node") or {}).get("fields", {}).get("nodes") or []
    for node in nodes:
        name = node.get("name")
        if not name:
            continue
        options = {o["name"]: o["id"] for o in (node.get("options") or []) if o.get("name")}
        out[name] = {
            "id": node.get("id"),
            "dataType": node.get("dataType"),
            "options": options,
        }
    return out


def _api_delay_seconds() -> float:
    raw = os.environ.get("META_API_DELAY_MS", "500")
    try:
        return max(0.0, int(raw) / 1000.0)
    except ValueError:
        return 0.5


def _api_pause(client: GitHubClient) -> None:
    if client.dry_run:
        return
    delay = _api_delay_seconds()
    if delay > 0:
        time.sleep(delay)


class IssueIndex:
    """Per-repo issue title index — avoids Search API rate limits."""

    def __init__(self, client: GitHubClient, org: str) -> None:
        self._client = client
        self._org = org
        self._by_repo: dict[str, dict[str, dict[str, Any]]] = {}

    def preload(self, repos: set[str]) -> None:
        for repo in sorted(repos):
            self._load_repo(repo)

    def find(self, repo: str, title: str) -> dict[str, Any] | None:
        self._load_repo(repo)
        return self._by_repo[repo].get(title)

    def _load_repo(self, repo: str) -> None:
        if repo in self._by_repo:
            return
        titles: dict[str, dict[str, Any]] = {}
        page = 1
        while True:
            _api_pause(self._client)
            data = self._client.rest(
                "GET",
                f"/repos/{self._org}/{repo}/issues",
                params={"state": "all", "per_page": 100, "page": page},
            )
            if not isinstance(data, list):
                break
            for issue in data:
                if issue.get("pull_request"):
                    continue
                titles[issue["title"]] = issue
            if len(data) < 100:
                break
            page += 1
        self._by_repo[repo] = titles
        print(f"  [index] {self._org}/{repo}: {len(titles)} issues cached")


def _create_issue(
    client: GitHubClient,
    org: str,
    repo: str,
    title: str,
    body: str,
    labels: list[str],
    *,
    issue_type: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    if issue_type:
        payload["type"] = issue_type
    _api_pause(client)
    return client.rest("POST", f"/repos/{org}/{repo}/issues", json_body=payload)


def _set_issue_type(
    client: GitHubClient,
    org: str,
    repo: str,
    number: int,
    issue_type: str,
) -> bool:
    if client.dry_run:
        return True
    try:
        _api_pause(client)
        client.rest(
            "PATCH",
            f"/repos/{org}/{repo}/issues/{number}",
            json_body={"type": issue_type},
        )
        return True
    except GitHubError as exc:
        print(
            f"  [warn] could not set type {issue_type!r}: {exc}. "
            "Run bootstrap-project --apply (org admin PAT) to create Epic type."
        )
        return False


def _link_parent_sub_issue(
    client: GitHubClient,
    org: str,
    item: dict[str, Any],
    id_to_issue: dict[str, dict[str, Any]],
    child_ref: dict[str, Any],
) -> None:
    """Attach child issue under manifest parent (e.g. EPIC) via GitHub sub-issues API."""
    parent_key = item.get("parent")
    if not parent_key:
        return
    parent = id_to_issue.get(str(parent_key))
    if not parent:
        print(f"  [warn] parent {parent_key!r} not resolved — skip sub-issue link")
        return
    if not client.dry_run and not parent.get("number"):
        print(f"  [warn] parent {parent_key!r} has no issue number — skip sub-issue link")
        return
    parent_repo = parent["repo"]
    parent_number = parent["number"]
    if client.dry_run:
        print(f"  [dry-run] sub-issue of {parent_key} ({org}/{parent_repo}#{parent_number})")
        return
    child_id = child_ref.get("id")
    if not child_id:
        print(f"  [warn] child issue id missing — skip sub-issue link")
        return
    try:
        _api_pause(client)
        client.rest(
            "POST",
            f"/repos/{org}/{parent_repo}/issues/{parent_number}/sub_issues",
            json_body={"sub_issue_id": child_id},
        )
        print(f"  linked sub-issue → {parent_key} (#{parent_number})")
    except GitHubError as exc:
        body = (exc.body or "").lower()
        idempotent = (
            "already" in body
            or "exist" in body
            or "duplicate" in body
            or "one parent" in body
        )
        if exc.status == 422 and idempotent:
            print(f"  sub-issue link already set ({parent_key})")
        else:
            raise


def _find_project_item_id(
    client: GitHubClient,
    project_id: str,
    issue_node_id: str,
) -> str | None:
    cursor: str | None = None
    while True:
        _api_pause(client)
        data = client.graphql(
            """
            query($projectId: ID!, $cursor: String) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  items(first: 100, after: $cursor) {
                    nodes {
                      id
                      content { ... on Issue { id } }
                    }
                    pageInfo { hasNextPage endCursor }
                  }
                }
              }
            }
            """,
            {"projectId": project_id, "cursor": cursor},
        )
        items = (data.get("node") or {}).get("items") or {}
        for node in items.get("nodes") or []:
            content = node.get("content") or {}
            if content.get("id") == issue_node_id:
                return node.get("id")
        page_info = items.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            return None
        cursor = page_info.get("endCursor")


def _add_issue_to_project(
    client: GitHubClient,
    project_id: str,
    issue_node_id: str,
) -> str:
    if client.dry_run:
        return "PVTI_dryrun"
    try:
        _api_pause(client)
        data = client.graphql(
            """
            mutation($projectId: ID!, $contentId: ID!) {
              addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
                item { id }
              }
            }
            """,
            {"projectId": project_id, "contentId": issue_node_id},
        )
        item = (data.get("addProjectV2ItemById") or {}).get("item") or {}
        item_id = item.get("id")
        if item_id:
            return item_id
    except GitHubError as exc:
        if "already" not in str(exc.body).lower():
            raise
        print("  (already on project)")
    item_id = _find_project_item_id(client, project_id, issue_node_id)
    if not item_id:
        raise GitHubError("issue on project but project item id not found")
    return item_id


def _set_project_field(
    client: GitHubClient,
    project_id: str,
    item_id: str,
    field: dict[str, Any],
    raw_value: str,
) -> None:
    if raw_value is None or raw_value == "":
        return
    field_id = field.get("id")
    if not field_id:
        return
    data_type = field.get("dataType", "")
    if data_type == "TEXT":
        value = {"text": str(raw_value)}
    elif data_type == "SINGLE_SELECT":
        opt_id = (field.get("options") or {}).get(str(raw_value))
        if not opt_id:
            raise GitHubError(f"unknown single-select value {raw_value!r} for field")
        value = {"singleSelectOptionId": opt_id}
    else:
        print(f"  [skip] unsupported field type {data_type}")
        return
    client.graphql(
        """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
          updateProjectV2ItemFieldValue(
            input: {projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: $value}
          ) {
            projectV2Item { id }
          }
        }
        """,
        {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": value,
        },
    )


def _merge_item(defaults: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    merged = {**defaults, **item}
    labels = list(defaults.get("labels") or [])
    for label in item.get("labels") or []:
        if label not in labels:
            labels.append(label)
    merged["labels"] = labels
    return merged


def _body_with_deps(body: str, depends_on: list[str], id_to_issue: dict[str, dict[str, Any]]) -> str:
    if not depends_on:
        return body
    lines: list[str] = []
    for dep_id in depends_on:
        ref = id_to_issue.get(dep_id)
        if ref:
            lines.append(f"- #{ref['number']} ({dep_id}) — {ref['url']}")
        else:
            lines.append(f"- {dep_id} (not created yet)")
    if not lines:
        return body
    block = "## Linked dependencies\n\n" + "\n".join(lines)
    if block in body:
        return body
    return body.rstrip() + "\n\n" + block + "\n"


def _resolve_row(item: dict[str, Any]) -> dict[str, str]:
    row: dict[str, str] = {}
    for yaml_key, field_name in _FIELD_MAP.items():
        val = item.get(yaml_key)
        if val is not None and str(val).strip() != "":
            row[field_name] = coerce_yaml_select_option(val)
    return row


def _apply_project_fields(
    client: GitHubClient,
    *,
    project_id: str,
    item_id: str,
    project_fields: dict[str, dict[str, Any]],
    item: dict[str, Any],
) -> None:
    for yaml_key, field_name in _FIELD_MAP.items():
        val = item.get(yaml_key)
        if val is None or str(val).strip() == "":
            continue
        field = project_fields.get(field_name)
        if not field:
            print(f"  [warn] project field missing: {field_name}")
            continue
        display = coerce_yaml_select_option(val)
        _api_pause(client)
        _set_project_field(client, project_id, item_id, field, display)
        print(f"  set {field_name}: {display}")


def _seed_one(
    client: GitHubClient,
    *,
    org: str,
    project_id: str,
    project_fields: dict[str, dict[str, Any]],
    item: dict[str, Any],
    id_to_issue: dict[str, dict[str, Any]],
    initiative: str,
    issue_index: IssueIndex | None = None,
    issue_type_roles: dict[str, str] | None = None,
) -> tuple[dict[str, Any], bool]:
    work_id = item.get("id", "")
    repo = item["repo"]
    title = item["title"]
    kind = item.get("kind", "issue")

    print(f"--- [{work_id or kind}] {org}/{repo}: {title}")

    issue_type = resolve_issue_type_name(item, issue_type_roles or {})
    if issue_type:
        print(f"  type: {issue_type}")

    existing = None if client.dry_run else (issue_index.find(repo, title) if issue_index else None)
    if existing:
        print(f"  exists: #{existing['number']} {existing['html_url']}")
        ref = {
            "number": existing["number"],
            "url": existing["html_url"],
            "node_id": existing["node_id"],
            "id": existing.get("id"),
            "repo": repo,
            "project_item_id": None,
        }
        if work_id:
            id_to_issue[work_id] = ref
        item_id = _add_issue_to_project(client, project_id, ref["node_id"])
        print(f"  on project item: {item_id}")
        ref["project_item_id"] = item_id
        _apply_project_fields(
            client,
            project_id=project_id,
            item_id=item_id,
            project_fields=project_fields,
            item=item,
        )
        if issue_type and _set_issue_type(client, org, repo, ref["number"], issue_type):
            print(f"  set type: {issue_type}")
        _link_parent_sub_issue(client, org, item, id_to_issue, ref)
        return ref, True

    body = _body_with_deps(
        str(item.get("body") or ""),
        list(item.get("depends_on") or []),
        id_to_issue,
    )
    footer = f"\n\n---\n_Initiative: {initiative}_"
    if initiative not in body:
        body = body.rstrip() + footer

    labels = list(item.get("labels") or [])
    if client.dry_run:
        print(f"  [dry-run] create issue + add to project")
        print(f"  labels: {', '.join(labels) or '(none)'}")
        for field_name, val in _resolve_row(item).items():
            print(f"  field {field_name}: {val}")
        ref = {
            "number": 0,
            "url": f"https://github.com/{org}/{repo}/issues/new",
            "node_id": "I_dryrun",
            "id": 0,
            "repo": repo,
            "project_item_id": "PVTI_dryrun",
        }
        if work_id:
            id_to_issue[work_id] = ref
        _link_parent_sub_issue(client, org, item, id_to_issue, ref)
        return ref, False

    try:
        created = _create_issue(
            client, org, repo, title, body, labels, issue_type=issue_type
        )
    except GitHubError as exc:
        if issue_type and "type" in str(exc.body).lower():
            print(f"  [warn] create with type failed — retry without type: {exc}")
            created = _create_issue(client, org, repo, title, body, labels)
        else:
            raise
    number = created["number"]
    url = created["html_url"]
    node_id = created["node_id"]
    print(f"  created: #{number} {url}")

    item_id = _add_issue_to_project(client, project_id, node_id)
    print(f"  on project item: {item_id}")

    _apply_project_fields(
        client,
        project_id=project_id,
        item_id=item_id,
        project_fields=project_fields,
        item=item,
    )

    ref = {
        "number": number,
        "url": url,
        "node_id": node_id,
        "id": created.get("id"),
        "repo": repo,
        "project_item_id": item_id,
    }
    if work_id:
        id_to_issue[work_id] = ref
    _link_parent_sub_issue(client, org, item, id_to_issue, ref)
    return ref, False


def _collect_repos(manifest: dict[str, Any]) -> set[str]:
    repos: set[str] = set()
    epic = manifest.get("epic")
    if isinstance(epic, dict) and epic.get("repo"):
        repos.add(epic["repo"])
    for raw in manifest.get("work") or []:
        if isinstance(raw, dict) and raw.get("repo"):
            repos.add(raw["repo"])
    return repos


def run(
    client: GitHubClient,
    *,
    manifest_path: str | None = None,
    org: str = "",
    project_config_path: str | None = None,
) -> None:
    root = tenant_root()
    if not manifest_path:
        raise SystemExit(
            "seed-work requires manifest_path (e.g. work/INIT-<id>.yaml from generate-work-manifest)"
        )
    mpath = manifest_path
    manifest = load_work_manifest(mpath)

    target = manifest["target"]
    org = org or target.get("org", "")
    project_title = target.get("project", "")
    initiative = manifest["initiative"]
    defaults = manifest["defaults"]

    pcfg_path = (
        project_config_path
        or target.get("project_config")
        or str(default_project_config_path(org))
    )
    project_cfg: dict[str, Any] = {}
    issue_type_roles: dict[str, str] = {}
    if Path(pcfg_path).is_file():
        project_cfg = load_project_config(pcfg_path)
        issue_type_roles = project_cfg.get("issue_type_roles") or {}

    print("=== seed-work ===")
    print(f"Manifest: {mpath}")
    print(f"Initiative: {initiative}")
    print(f"Org: {org}")
    print(f"Project: {project_title}")
    print(f"Authenticated as: {client.whoami()}")
    print(f"Mode: {'dry-run' if client.dry_run else 'apply'}")
    if issue_type_roles:
        print(f"Issue type roles: {issue_type_roles} (from {pcfg_path})")
    print("")

    if not org:
        raise ValueError("org is required (manifest target.org or --org)")
    if not project_title:
        raise ValueError("project title is required in manifest target.project")

    if not client.org_ok(org):
        raise RuntimeError(f"cannot access org {org}")
    verify_project_scope(client, org)

    if not client.dry_run:
        verify_path = str(default_verify_config_path(org))
        try:
            run_applied(client, config_path=verify_path, org=org)
        except VerifyError as exc:
            raise RuntimeError(
                f"platform not ready for backlog: {exc}. "
                f"Run: ./scripts/meta setup-platform --apply"
            ) from exc
        print("")

    project_num = _project_number_by_title(client, org, project_title)
    if project_num is None and not client.dry_run:
        raise RuntimeError(
            f"project {project_title!r} not found in {org}. "
            f"Run: launchpad bootstrap-project --apply"
        )

    if client.dry_run and not project_num:
        project_id = "PVT_dryrun"
        project_fields = {}
        project_url = "(dry-run)"
    elif client.dry_run and project_num:
        meta = _project_meta(client, org, project_num)
        project_id = meta["id"]
        project_url = meta["url"]
        project_fields = _project_fields(client, project_id)
    else:
        meta = _project_meta(client, org, project_num)
        project_id = meta["id"]
        project_url = meta["url"]
        project_fields = _project_fields(client, project_id)

    print(f"Project: {project_url}")
    print("")

    issue_index: IssueIndex | None = None
    if not client.dry_run:
        repos = _collect_repos(manifest)
        print(f"Preloading issue index for {len(repos)} repos (META_API_DELAY_MS={os.environ.get('META_API_DELAY_MS', '500')})")
        issue_index = IssueIndex(client, org)
        issue_index.preload(repos)
        print("")

    id_to_issue: dict[str, dict[str, Any]] = {}
    created_count = 0
    skipped_count = 0
    planned_count = 0

    def _process(item: dict[str, Any]) -> None:
        nonlocal created_count, skipped_count, planned_count
        _, existed = _seed_one(
            client,
            org=org,
            project_id=project_id,
            project_fields=project_fields,
            item=item,
            id_to_issue=id_to_issue,
            initiative=initiative,
            issue_index=issue_index,
            issue_type_roles=issue_type_roles,
        )
        if client.dry_run:
            planned_count += 1
        elif existed:
            skipped_count += 1
        else:
            created_count += 1

    epic = manifest.get("epic")
    if epic:
        epic_item = _merge_item(
            defaults,
            {**epic, "kind": "epic", "id": epic.get("id", "EPIC")},
        )
        epic_item.setdefault("initiative", initiative)
        epic_item.pop("parent", None)
        _process(epic_item)

    for raw in manifest["work"]:
        if not isinstance(raw, dict):
            continue
        item = _merge_item(defaults, raw)
        item.setdefault("initiative", initiative)
        _process(item)

    print("")
    print("=== Done ===")
    print(f"Initiative: {initiative}")
    print(f"Project: {project_url}")
    if client.dry_run:
        print(f"Would process: {planned_count} items (1 epic + sub-issues)")
        print("Re-run with --apply to create issues, link hierarchy, and set project fields.")
        print("After apply: Project → Table view → View → Show hierarchy")
    else:
        print(f"Created: {created_count} | Already existed (skipped): {skipped_count}")
        print("")
        print("ID → issue:")
        for wid, ref in sorted(id_to_issue.items()):
            print(f"  {wid}: #{ref['number']} {ref['url']}")
