"""Seed GitLab issues from a WorkManifest YAML (label-based board fields)."""

from __future__ import annotations

import os
import time
from typing import Any

from launchpad.adapters.gitlab.client import GitLabClient, GitLabError
from launchpad.config import load_work_manifest, load_project_config

STATUS_PREFIX = "status::"
CODEBASE_PREFIX = "codebase::"
INITIATIVE_PREFIX = "initiative::"


def _status_label(status: str) -> str:
    return f"{STATUS_PREFIX}{status.replace(' ', '-').lower()}"


def _codebase_label(codebase: str) -> str:
    return f"{CODEBASE_PREFIX}{codebase}"


def _initiative_label(initiative: str) -> str:
    return f"{INITIATIVE_PREFIX}{initiative}"


def _issue_body(item: dict[str, Any], defaults: dict[str, Any]) -> str:
    lines = [
        f"**Initiative:** {item.get('initiative', defaults.get('initiative', ''))}",
        f"**CR:** {item.get('cr', defaults.get('cr', 'N/A'))}",
        f"**Codebase:** {item.get('codebase', '')}",
        f"**Spec path:** {item.get('spec_path', '')}",
        f"**Verify command:** {item.get('verify_command', '')}",
        f"**As-built:** {item.get('as_built', defaults.get('as_built', 'no'))}",
        f"**QA manifest:** {item.get('qa_manifest', defaults.get('qa_manifest', 'N/A'))}",
    ]
    extra = item.get("body") or ""
    if extra:
        lines.append("")
        lines.append(extra)
    return "\n".join(lines)


def _labels_for_item(item: dict[str, Any], defaults: dict[str, Any], initiative: str) -> list[str]:
    status = str(item.get("status", defaults.get("status", "Backlog")))
    codebase = str(item.get("codebase", ""))
    labels = [
        _status_label(status),
        _initiative_label(initiative),
    ]
    if codebase:
        labels.append(_codebase_label(codebase))
    for lb in item.get("labels") or defaults.get("labels") or []:
        if lb not in labels:
            labels.append(str(lb))
    return labels


def _ensure_status_labels(client: GitLabClient, project_id: int, columns: list[str]) -> None:
    for col in columns:
        client.ensure_label(project_id, _status_label(col))


def run(
    client: GitLabClient,
    *,
    manifest_path: str,
    group: str = "",
    project_config_path: str | None = None,
) -> None:
    manifest = load_work_manifest(manifest_path)
    target = manifest["target"]
    group = group or target.get("group") or target.get("org", "")
    initiative = manifest["initiative"]
    defaults = manifest["defaults"]

    columns: list[str] = []
    if project_config_path:
        pcfg = load_project_config(project_config_path)
        columns = list(pcfg.get("status_columns") or [])

    print("=== seed-work (gitlab) ===")
    print(f"Manifest: {manifest_path}")
    print(f"Initiative: {initiative}")
    print(f"Group: {group}")
    if not client.dry_run:
        print(f"Authenticated as: {client.whoami()}")
    print(f"Mode: {'dry-run' if client.dry_run else 'apply'}")
    print("")

    if not group:
        raise ValueError("GitLab group is required (manifest target.group or target.org)")

    id_to_iid: dict[str, dict[str, Any]] = {}

    epic = manifest.get("epic")
    if isinstance(epic, dict) and epic.get("repo"):
        repo = str(epic["repo"])
        title = str(epic.get("title", f"[feature] {initiative}"))
        proj = client.project(group, repo)
        pid = int(proj["id"])
        if columns:
            _ensure_status_labels(client, pid, columns)
        labels = _labels_for_item({**defaults, **epic, "codebase": epic.get("codebase", repo)}, defaults, initiative)
        labels.append("epic")
        issue = client.create_issue(
            pid,
            title=title,
            description=_issue_body(epic, defaults),
            labels=labels,
        )
        id_to_iid[str(epic.get("id", "EPIC"))] = issue
        print(f"  epic: {title} → {issue.get('web_url', '(dry-run)')}")

    for raw in manifest.get("work") or []:
        if not isinstance(raw, dict):
            continue
        work_id = str(raw.get("id", ""))
        repo = str(raw.get("repo", ""))
        title = str(raw.get("title", work_id))
        proj = client.project(group, repo)
        pid = int(proj["id"])
        if columns:
            _ensure_status_labels(client, pid, columns)
        labels = _labels_for_item(raw, defaults, initiative)
        issue = client.create_issue(
            pid,
            title=title,
            description=_issue_body(raw, defaults),
            labels=labels,
        )
        id_to_iid[work_id] = issue
        print(f"  {work_id}: {title} → {issue.get('web_url', '(dry-run)')}")
        delay = max(0.0, int(os.environ.get("META_API_DELAY_MS", "500")) / 1000.0)
        if delay and not client.dry_run:
            time.sleep(delay)

    print("")
    print(f"Done — {len(id_to_iid)} issue(s)")
