"""Project slug and repo prefix resolution for OnboardingSpec."""

from __future__ import annotations

import re
from typing import Any

from launchpad.onboarding.errors import OnboardingError

_PROJECT_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_REGISTRY_ID_RE = _PROJECT_SLUG_RE


def normalize_registry_id(raw: str) -> str:
    return raw.strip().lower().replace("_", "-")


def validate_registry_id(value: str, *, field: str = "client_id") -> str:
    """Return normalized id or raise with a helpful message."""
    raw = value.strip()
    normalized = normalize_registry_id(raw)
    if not _REGISTRY_ID_RE.match(normalized):
        raise OnboardingError(
            f"{field} must match [a-z][a-z0-9-]{{0,62}} (e.g. kola) — "
            "this is your local registry / programme slug, not the GitHub org name"
        )
    if raw != normalized and field in ("client_id", "project_slug", "repo_prefix"):
        raise OnboardingError(
            f"{field} must be entered lowercase (got {raw!r}). "
            "Use your programme slug (e.g. kola), not the GitHub org name."
        )
    return normalized


def resolve_project_slug(raw: dict[str, Any], *, client_id: str) -> str:
    slug = str(raw.get("project_slug") or client_id).strip()
    if not _PROJECT_SLUG_RE.match(slug):
        raise OnboardingError(
            "project_slug must match [a-z][a-z0-9-]{0,62} (defaults to client_id)"
        )
    return slug


def resolve_repo_prefix(raw: dict[str, Any], *, project_slug: str, repos_container: Any) -> str:
    explicit = str(raw.get("repo_prefix") or "").strip()
    if explicit:
        return explicit.rstrip("-")
    if isinstance(repos_container, dict):
        nested = str(repos_container.get("prefix") or "").strip()
        if nested:
            return nested.rstrip("-")
    return project_slug.rstrip("-")


def prefixed_repo_name(prefix: str, suffix: str) -> str:
    base = prefix.rstrip("-")
    tail = suffix.strip().lstrip("-")
    if not tail:
        raise OnboardingError("repo suffix must be non-empty")
    if base and tail.startswith(f"{base}-"):
        return tail
    return f"{base}-{tail}" if base else tail


def default_meta_repo_name(*, repo_prefix: str, project_slug: str) -> str:
    return prefixed_repo_name(repo_prefix or project_slug, "meta")


def parse_repo_entries(
    repos_raw: Any,
    *,
    repo_prefix: str,
    meta_repo: str,
) -> list[dict[str, Any]]:
    """Return app repo list from a sequence or {prefix, apps} mapping."""
    if isinstance(repos_raw, dict):
        entries = repos_raw.get("apps") or repos_raw.get("list") or []
    elif isinstance(repos_raw, list):
        entries = repos_raw
    else:
        raise OnboardingError("repos must be a list or a mapping with apps")

    if not entries:
        raise OnboardingError("repos must be a non-empty list of app repos (meta is not listed here)")

    repos: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            raise OnboardingError(f"repos[{idx}] must be a mapping")
        name = str(item.get("name") or "").strip()
        suffix = str(item.get("suffix") or "").strip()
        if name and suffix:
            raise OnboardingError(f"repos[{idx}]: use name or suffix, not both")
        if suffix:
            name = prefixed_repo_name(repo_prefix, suffix)
        if not name:
            raise OnboardingError(f"repos[{idx}].name or repos[{idx}].suffix is required")
        if name == meta_repo:
            raise OnboardingError(f"repos must not include meta repo {meta_repo!r}")
        if name in seen:
            raise OnboardingError(f"duplicate repo name: {name}")
        seen.add(name)
        repos.append({**item, "name": name})
    return repos
