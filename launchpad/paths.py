"""Resolve launchpad kit paths and tenant template overrides."""

from __future__ import annotations

import os
from pathlib import Path

import launchpad
from launchpad.config import tenant_root


def kit_root() -> Path:
    """Launchpad install / source tree (contains `templates/`, `playbook/`, `examples/`)."""
    explicit = os.environ.get("LAUNCHPAD_KIT_ROOT", "").strip()
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"LAUNCHPAD_KIT_ROOT is not a directory: {root}")
        return root

    pkg_dir = Path(launchpad.__file__).resolve().parent
    bundled = pkg_dir / "_kit"
    if (bundled / "templates").is_dir():
        return bundled

    root = pkg_dir.parent
    if (root / "templates").is_dir():
        return root
    raise FileNotFoundError(
        "launchpad kit templates/ not found — set LAUNCHPAD_KIT_ROOT to the launchpad repo root"
    )


def _normalize_template_rel(rel_path: str | Path) -> Path:
    rel = Path(rel_path)
    if rel.parts and rel.parts[0] == "templates":
        return rel
    return Path("templates") / rel


def resolve_template(rel_path: str | Path) -> Path:
    """Tenant override first, then kit default. rel_path e.g. templates/AGENTS.python.md."""
    rel = _normalize_template_rel(rel_path)
    tenant_path = tenant_root() / rel
    if tenant_path.is_file():
        return tenant_path.resolve()
    kit_path = kit_root() / rel
    if kit_path.is_file():
        return kit_path.resolve()
    raise FileNotFoundError(
        f"template not found: {rel} (checked tenant {tenant_path} and kit {kit_path})"
    )
