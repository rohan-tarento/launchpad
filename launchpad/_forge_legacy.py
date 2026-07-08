"""Forge type resolution (github | gitlab)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from launchpad.config import load_org_config, load_work_manifest, load_yaml


def forge_from_mapping(cfg: dict[str, Any]) -> str:
    forge = cfg.get("forge") or {}
    if isinstance(forge, dict):
        ftype = str(forge.get("type", "github")).lower()
        if ftype in ("github", "gitlab"):
            return ftype
    return "github"


def gitlab_host_from_mapping(cfg: dict[str, Any]) -> str:
    forge = cfg.get("forge") or {}
    if isinstance(forge, dict) and forge.get("host"):
        return str(forge["host"])
    return "https://gitlab.com"


def resolve_forge_for_manifest(manifest_path: str, org_config_path: str | None = None) -> tuple[str, str]:
    """Return (forge_type, gitlab_host)."""
    manifest = load_work_manifest(manifest_path)
    target = manifest.get("target") or {}
    if target.get("forge"):
        ftype = str(target["forge"]).lower()
        if ftype in ("github", "gitlab"):
            host = str(target.get("host", "https://gitlab.com"))
            return ftype, host

    org = target.get("org") or target.get("group") or ""
    if org_config_path and Path(org_config_path).is_file():
        return forge_from_mapping(load_org_config(org_config_path)), gitlab_host_from_mapping(
            load_yaml(org_config_path)
        )

    if org:
        from launchpad.config import discover_tenant_config

        try:
            org_path = discover_tenant_config("org", org=org)
            cfg = load_org_config(org_path)
            return forge_from_mapping(cfg), gitlab_host_from_mapping(cfg)
        except (FileNotFoundError, ValueError):
            pass

    return "github", "https://gitlab.com"
