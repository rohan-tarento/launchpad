"""Programme schema — identity spine for a launchpad-managed programme.

File: config/programme.yaml
Kind: Programme

Fields
------
programme       Human name for the initiative (e.g. "KOLA", "Kola").
programme_slug  Lowercase registry id; derived from programme if omitted.
                Must match clients.yaml entry id.
org             GitHub organisation slug (exact spelling, e.g. "apex-common").
meta_repo       Control-plane repo name (e.g. "kola-meta").
forge           Forge configuration.
  provider      "github" (only supported provider in v0.5.10).
                "gitlab" is planned — rejected with a clear message if supplied.

Local clone layout (workspace) lives in ~/.config/launchpad/clients.yaml —
never in this shared file.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from launchpad.schema.errors import SchemaError

_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_SUPPORTED_PROVIDERS = {"github"}
_PLANNED_PROVIDERS = {"gitlab"}

API_VERSION = "launchpad/v1"
KIND = "Programme"


def _derive_slug(name: str) -> str:
    """Derive a programme_slug from a human programme name."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class ProgrammeSchema:
    """Validated, normalised representation of programme.yaml."""

    def __init__(self, raw: dict[str, Any], *, path: str = "") -> None:
        self._path = path
        self.programme: str = ""
        self.programme_slug: str = ""
        self.org: str = ""
        self.meta_repo: str = ""
        self.forge_provider: str = "github"
        self._validate(raw)

    def _validate(self, raw: dict[str, Any]) -> None:
        p = self._path

        if "workspace" in raw:
            raise SchemaError(
                "programme.yaml must not contain 'workspace' — it is machine-local",
                path=p,
                hint=(
                    "Move workspace to ~/.config/launchpad/clients.yaml under your "
                    "client entry (path = meta clone; workspace = parent of sibling "
                    "repos). Remove workspace: from programme.yaml and commit."
                ),
            )

        programme = str(raw.get("programme") or "").strip()
        if not programme:
            raise SchemaError(
                "programme.yaml missing required field 'programme'",
                path=p,
                hint="Set programme: to your initiative name, e.g. 'KOLA'",
            )
        self.programme = programme

        slug_raw = str(raw.get("programme_slug") or "").strip()
        slug = slug_raw or _derive_slug(programme)
        if not _SLUG_RE.match(slug):
            raise SchemaError(
                f"programme_slug {slug!r} is invalid — must be lowercase [a-z][a-z0-9-]",
                path=p,
                hint="Use a lowercase slug, e.g. 'kola' (not the GitHub org name)",
            )
        self.programme_slug = slug

        org = str(raw.get("org") or "").strip()
        if not org:
            raise SchemaError(
                "programme.yaml missing required field 'org'",
                path=p,
                hint="Set org: to your GitHub organisation, e.g. 'apex-common'",
            )
        self.org = org

        meta_repo = str(raw.get("meta_repo") or "").strip()
        if not meta_repo:
            meta_repo = f"{self.programme_slug}-meta"
        self.meta_repo = meta_repo

        forge = raw.get("forge") or {}
        if not isinstance(forge, dict):
            raise SchemaError("programme.yaml 'forge' must be a mapping", path=p)
        provider = str(forge.get("provider") or "github").strip().lower()
        if provider in _PLANNED_PROVIDERS:
            raise SchemaError(
                f"forge.provider '{provider}' is not yet supported in v0.5.10",
                path=p,
                hint="Only 'github' is supported. GitLab is a planned provider in a future release.",
            )
        if provider not in _SUPPORTED_PROVIDERS:
            raise SchemaError(
                f"Unknown forge.provider '{provider}'",
                path=p,
                hint=f"Supported: {sorted(_SUPPORTED_PROVIDERS)}. Planned: {sorted(_PLANNED_PROVIDERS)}",
            )
        self.forge_provider = provider

    def as_dict(self) -> dict[str, Any]:
        return {
            "apiVersion": API_VERSION,
            "kind": KIND,
            "programme": self.programme,
            "programme_slug": self.programme_slug,
            "org": self.org,
            "meta_repo": self.meta_repo,
            "forge": {"provider": self.forge_provider},
        }


def load_programme(path: str | Path) -> ProgrammeSchema:
    """Load and validate programme.yaml from *path*."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise SchemaError(f"programme.yaml not found: {p}")
    with p.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise SchemaError(f"programme.yaml must be a YAML mapping: {p}")
    return ProgrammeSchema(raw, path=str(p))
