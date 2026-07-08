"""ServiceCatalog schema — service map for the programme.

File: config/service-catalog-<org>.yaml
Kind: ServiceCatalog

The catalog is REQUIRED.  On day 1 only the meta repo is a live entry.
App repos are placed as YAML comments (examples) and promoted to live
entries once they are scaffolded or onboarded.

Fields
------
org             Must match programme.yaml org.
services        Map of repo slug → ServiceEntry.
  stack         Required.  Must match a stack_profiles key in governance.
  description   Short description of the service.
  status        "live" | "planned" | "deprecated" (default: "live").
  teams         List of owning teams (informational, not enforced here).
  links         Free-form dict of named URLs (docs, dashboard, runbook, etc.).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from launchpad.schema.errors import SchemaError

API_VERSION = "launchpad/v1"
KIND = "ServiceCatalog"

_VALID_STATUS = {"live", "planned", "deprecated"}


class ServiceEntry:
    def __init__(self, name: str, raw: dict[str, Any], *, path: str = "") -> None:
        stack = str(raw.get("stack") or "").strip()
        if not stack:
            raise SchemaError(
                f"service-catalog.services.{name!r} missing required field 'stack'",
                path=path,
                hint="Set stack: to the repo's stack profile (e.g. 'python-backend')",
            )
        self.name = name
        self.stack = stack
        self.description = str(raw.get("description") or "").strip()
        status = str(raw.get("status") or "live").strip().lower()
        if status not in _VALID_STATUS:
            raise SchemaError(
                f"service-catalog.services.{name!r} status={status!r} is invalid",
                path=path,
                hint=f"Use one of: {sorted(_VALID_STATUS)}",
            )
        self.status = status
        self.teams: list[str] = list(raw.get("teams") or [])
        self.links: dict[str, str] = {
            k: str(v) for k, v in (raw.get("links") or {}).items()
        }


class CatalogSchema:
    """Validated, normalised representation of service-catalog-<org>.yaml."""

    def __init__(self, raw: dict[str, Any], *, path: str = "") -> None:
        self._path = path
        self.org: str = ""
        self.services: dict[str, ServiceEntry] = {}
        self._validate(raw)

    def _validate(self, raw: dict[str, Any]) -> None:
        p = self._path

        org = str(raw.get("org") or "").strip()
        if not org:
            raise SchemaError(
                "service-catalog YAML missing required field 'org'",
                path=p,
                hint="Set org: to match your programme.yaml org",
            )
        self.org = org

        services_raw = raw.get("services") or {}
        if not isinstance(services_raw, dict):
            raise SchemaError("'services' must be a mapping", path=p)

        if len(services_raw) == 0:
            raise SchemaError(
                "service-catalog must contain at least one entry in 'services'",
                path=p,
                hint="Add your meta repo as the first live service — see the examples below",
            )

        for svc_name, svc_data in services_raw.items():
            if not isinstance(svc_data, dict):
                raise SchemaError(f"services.{svc_name!r} must be a mapping", path=p)
            self.services[svc_name] = ServiceEntry(svc_name, svc_data, path=p)

    @property
    def live_services(self) -> list[ServiceEntry]:
        return [s for s in self.services.values() if s.status == "live"]


def load_catalog(path: str | Path) -> CatalogSchema:
    """Load and validate a service-catalog-<org>.yaml from *path*."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise SchemaError(f"Service catalog YAML not found: {p}")
    with p.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise SchemaError(f"Service catalog YAML must be a YAML mapping: {p}")
    return CatalogSchema(raw, path=str(p))
