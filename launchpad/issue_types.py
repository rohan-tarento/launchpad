"""GitHub organization issue types — bootstrap + role resolution."""

from __future__ import annotations

from typing import Any

from launchpad.github_client import GitHubClient, GitHubError

ISSUE_TYPES_PAT_HINT = (
    "Fine-grained PAT: Organization → Issue types → Read and write. "
    "Classic PAT: admin:org. See playbook/python-automation.md."
)


def list_org_issue_types(client: GitHubClient, org: str) -> dict[str, dict[str, Any]]:
    """Return issue types keyed by name (enabled types only)."""
    try:
        data = client.rest("GET", f"/orgs/{org}/issue-types")
    except GitHubError as exc:
        if exc.status in (401, 403, 404):
            raise RuntimeError(
                f"cannot list issue types for {org}. {ISSUE_TYPES_PAT_HINT}"
            ) from exc
        raise
    if not isinstance(data, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name and item.get("is_enabled", True):
            out[str(name)] = item
    return out


def verify_issue_types_scope(client: GitHubClient, org: str) -> None:
    """Fail fast if PAT cannot read org issue types."""
    list_org_issue_types(client, org)


def verify_issue_types_present(
    client: GitHubClient,
    org: str,
    names: list[str],
) -> None:
    """Fail if any required issue type names are missing from the org."""
    required = [n.strip() for n in names if n and str(n).strip()]
    if not required:
        return
    existing = list_org_issue_types(client, org)
    missing = [n for n in required if n not in existing]
    if missing:
        raise RuntimeError(
            f"required issue types missing in {org}: {missing}. "
            "Run: ./scripts/meta bootstrap-project --apply"
        )


def ensure_org_issue_types(
    client: GitHubClient,
    org: str,
    specs: list[dict[str, Any]],
) -> None:
    """Create missing org issue types from project config `issue_types.ensure`."""
    if not specs:
        return

    names = [str(s.get("name", "")).strip() for s in specs]
    names = [n for n in names if n]

    if client.dry_run:
        for spec in specs:
            name = str(spec.get("name", "")).strip()
            if not name:
                continue
            color = str(spec.get("color", "gray"))
            print(f"[dry-run] create issue type: {name} ({color})")
        return

    verify_issue_types_scope(client, org)
    existing = list_org_issue_types(client, org)

    for spec in specs:
        name = str(spec.get("name", "")).strip()
        if not name:
            continue
        if name in existing:
            print(f"Issue type exists: {name}")
            continue
        color = str(spec.get("color", "gray"))
        description = str(spec.get("description", ""))
        print(f"[run] create issue type: {name}")
        try:
            client.rest(
                "POST",
                f"/orgs/{org}/issue-types",
                json_body={
                    "name": name,
                    "color": color,
                    "description": description or name,
                    "is_enabled": True,
                },
            )
        except GitHubError as exc:
            raise RuntimeError(
                f"failed to create issue type {name!r} in {org}. {ISSUE_TYPES_PAT_HINT}"
            ) from exc

    verify_issue_types_present(client, org, names)


def resolve_issue_type_name(item: dict[str, Any], roles: dict[str, str]) -> str | None:
    """Map manifest item → GitHub issue type name via project config roles."""
    explicit = item.get("issue_type")
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    kind = str(item.get("kind", "issue"))
    if kind == "epic":
        return roles.get("epic") or None
    return roles.get("task") or None
