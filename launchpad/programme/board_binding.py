"""Resolve programme engineering board binding from governance config."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from launchpad.github_client import GitHubClient, GitHubError
from launchpad.github_ops import _project_meta, _project_number_by_title


@dataclass(frozen=True)
class BoardBinding:
    org: str
    enabled: bool
    name: str
    number: int | None
    url: str

    @property
    def configured(self) -> bool:
        return self.enabled and bool(self.name.strip())


def project_board_url(org: str, number: int) -> str:
    return f"https://github.com/orgs/{org}/projects/{number}"


def _number_from_url(url: str) -> int | None:
    match = re.search(r"/projects/(\d+)(?:[/?#]|$)", url.strip())
    if not match:
        return None
    return int(match.group(1))


def resolve_board_binding(org: str, project_board: dict[str, Any] | None) -> BoardBinding:
    """Read board binding from governance YAML (no GitHub API)."""
    pb = dict(project_board or {})
    enabled = bool(pb.get("enabled"))
    name = str(pb.get("name") or "").strip()
    number_raw = pb.get("number")
    number: int | None = None
    if number_raw is not None and str(number_raw).strip() != "":
        number = int(number_raw)
    url = str(pb.get("url") or "").strip()
    if not url and number is not None:
        url = project_board_url(org, number)
    elif url and number is None:
        number = _number_from_url(url)
    return BoardBinding(
        org=org,
        enabled=enabled,
        name=name,
        number=number,
        url=url,
    )


def enrich_board_binding(
    binding: BoardBinding,
    client: GitHubClient,
) -> BoardBinding:
    """Resolve project number/url from GitHub when only the name is configured."""
    if not binding.configured:
        return binding
    if binding.number is not None and binding.url:
        return binding
    number = binding.number
    if number is None:
        number = _project_number_by_title(client, binding.org, binding.name)
    if number is None:
        return binding
    try:
        meta = _project_meta(client, binding.org, number)
    except GitHubError:
        return BoardBinding(
            org=binding.org,
            enabled=binding.enabled,
            name=binding.name,
            number=number,
            url=project_board_url(binding.org, number),
        )
    return BoardBinding(
        org=binding.org,
        enabled=binding.enabled,
        name=str(meta.get("title") or binding.name),
        number=number,
        url=str(meta.get("url") or project_board_url(binding.org, number)),
    )
