"""ScaffoldConfig schema — cookiecutter source configuration per repo.

File: config/scaffold-<org>.yaml
Kind: ScaffoldConfig

Scaffold is OPTIONAL and purely YAML-driven.
The kit is only an orchestrator — it does not maintain a list of allowed
template keys.  All fields under `context` are passed free-form to
cookiecutter, so template owners can evolve their parameters without
any changes to Launchpad.

Fields
------
org             Must match programme.yaml org.
meta            Scaffold config for the meta repo.
  enabled       True if scaffold should be applied.
  engine        "cookiecutter" (default, only supported engine).
  template      Template source:
                  "gh:<org>/<repo>"  → GitHub SSH clone
                  "git+https://..."  → arbitrary git URL
                  "/path/to/local"   → local filesystem path
  ref           Git ref to checkout (tag or branch).
  context       Free-form dict — passed directly to cookiecutter.
repos           Map of repo slug → same structure as meta.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from launchpad.schema.errors import SchemaError

API_VERSION = "launchpad/v1"
KIND = "ScaffoldConfig"

_SUPPORTED_ENGINES = {"cookiecutter"}


class ScaffoldEntry:
    """Scaffold config for one repo (or the meta repo)."""

    def __init__(self, name: str, raw: dict[str, Any], *, path: str = "") -> None:
        self.name = name
        self.enabled: bool = bool(raw.get("enabled", False))
        engine = str(raw.get("engine") or "cookiecutter").strip().lower()
        if engine not in _SUPPORTED_ENGINES:
            raise SchemaError(
                f"scaffold.{name!r}.engine={engine!r} is not supported",
                path=path,
                hint=f"Supported engines: {sorted(_SUPPORTED_ENGINES)}",
            )
        self.engine = engine

        template = str(raw.get("template") or "").strip()
        ref = str(raw.get("ref") or "").strip()
        context = raw.get("context") or {}

        if self.enabled:
            if not template:
                raise SchemaError(
                    f"scaffold.{name!r}: enabled=true requires 'template'",
                    path=path,
                    hint="Set template: to a gh:<org>/<repo>, git URL, or local path",
                )
            if not ref:
                raise SchemaError(
                    f"scaffold.{name!r}: enabled=true requires 'ref'",
                    path=path,
                    hint="Pin to a tag or branch, e.g. ref: v1.0.0",
                )
            if not isinstance(context, dict):
                raise SchemaError(
                    f"scaffold.{name!r}.context must be a mapping", path=path
                )

        self.template = template
        self.ref = ref
        self.context: dict[str, Any] = dict(context) if isinstance(context, dict) else {}

    def resolve_template_url(self) -> str:
        """Resolve template shorthand to a full git-clone URL."""
        t = self.template
        if t.startswith("gh:"):
            slug = t[3:]
            return f"https://github.com/{slug}"
        return t


class ScaffoldSchema:
    """Validated, normalised representation of scaffold-<org>.yaml."""

    def __init__(self, raw: dict[str, Any], *, path: str = "") -> None:
        self._path = path
        self.org: str = ""
        self.meta: ScaffoldEntry | None = None
        self.repos: dict[str, ScaffoldEntry] = {}
        self._validate(raw)

    def _validate(self, raw: dict[str, Any]) -> None:
        p = self._path

        org = str(raw.get("org") or "").strip()
        if not org:
            raise SchemaError(
                "scaffold YAML missing required field 'org'",
                path=p,
                hint="Set org: to match your programme.yaml org",
            )
        self.org = org

        meta_raw = raw.get("meta")
        if meta_raw is not None:
            if not isinstance(meta_raw, dict):
                raise SchemaError("scaffold 'meta' must be a mapping", path=p)
            self.meta = ScaffoldEntry("meta", meta_raw, path=p)

        repos_raw = raw.get("repos") or {}
        if not isinstance(repos_raw, dict):
            raise SchemaError("scaffold 'repos' must be a mapping", path=p)
        for repo_name, repo_data in repos_raw.items():
            if not isinstance(repo_data, dict):
                raise SchemaError(f"scaffold.repos.{repo_name!r} must be a mapping", path=p)
            self.repos[repo_name] = ScaffoldEntry(repo_name, repo_data, path=p)


def load_scaffold(path: str | Path) -> ScaffoldSchema:
    """Load and validate a scaffold-<org>.yaml from *path*."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise SchemaError(f"Scaffold YAML not found: {p}")
    with p.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise SchemaError(f"Scaffold YAML must be a YAML mapping: {p}")
    return ScaffoldSchema(raw, path=str(p))
