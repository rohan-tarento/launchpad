"""Load YAML config files for gitflow and project bootstrap."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from launchpad.gitflow_policy import normalize_gitflow_policy

import yaml


def tenant_root() -> Path:
    """Resolve the active <client>-meta directory (tenant workspace root)."""
    explicit = os.environ.get("LAUNCHPAD_TENANT_ROOT", "").strip()
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"LAUNCHPAD_TENANT_ROOT is not a directory: {root}")
        return root

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / ".launchpad-version").is_file():
            return candidate
        config_dir = candidate / "config"
        if config_dir.is_dir() and any(
            p.suffix == ".yaml" and ".example" not in p.name for p in config_dir.iterdir()
        ):
            return candidate
        if (candidate / "prd").is_dir() and (candidate / "work").is_dir():
            return candidate

    raise FileNotFoundError(
        "Tenant root not found. Use one of:\n"
        "  launchpad --client <id>     (from ~/.config/launchpad/clients.yaml)\n"
        "  export LAUNCHPAD_TENANT_ROOT=/path/to/<client>-meta\n"
        "  cd into <client>-meta"
    )


def tenant_config_dir() -> Path:
    """Tenant factory YAML directory: {tenant_root}/config/."""
    config_dir = tenant_root() / "config"
    if not config_dir.is_dir():
        raise FileNotFoundError(f"tenant config directory missing: {config_dir}")
    return config_dir


def resolve_workspace_parent(
    *,
    gitflow_options: dict[str, Any] | None = None,
    harness_cfg: dict[str, Any] | None = None,
) -> Path:
    """Parent directory for app repo clones (sibling of tenant meta)."""
    root = tenant_root()
    for options, key in ((gitflow_options, "workspace"), (harness_cfg, "default_workspace")):
        if not options:
            continue
        raw = str(options.get(key) or "").strip()
        if raw:
            p = Path(raw).expanduser()
            return (p if p.is_absolute() else (root / p)).resolve()
    return root.parent


def discover_tenant_config(kind: str, *, org: str = "") -> Path:
    """Find config/{kind}-<org>.yaml or the sole non-example file for kind."""
    config_dir = tenant_config_dir()
    if not config_dir.is_dir():
        raise FileNotFoundError(f"tenant config directory missing: {config_dir}")

    if org:
        path = config_dir / f"{kind}-{org}.yaml"
        if path.is_file():
            return path
        raise FileNotFoundError(f"config not found: {path}")

    matches = sorted(
        p for p in config_dir.glob(f"{kind}-*.yaml") if ".example" not in p.name
    )
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(
            f"no {kind}-*.yaml under {config_dir} — pass --config or --org"
        )
    names = ", ".join(p.name for p in matches)
    raise ValueError(f"multiple {kind} configs ({names}) — pass --config or --org")


def load_yaml(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"config not found: {p}")
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping in {p}")
    return data


def resolve_config_path(
    kind: str,
    *,
    org: str = "",
    explicit: str | Path | None = None,
    base: Path | str | None = None,
) -> Path:
    """Convention: config/{kind}-{org}.yaml"""
    if explicit:
        p = Path(explicit)
        if not p.is_absolute() and base is not None:
            candidate = Path(base).parent / p
            if candidate.is_file():
                return candidate.resolve()
        return p.resolve() if p.is_file() else p
    if not org:
        raise ValueError(f"--config or --org required for {kind}")
    return (tenant_config_dir() / f"{kind}-{org}.yaml").resolve()


def _resolve_include_path(include_path: str | Path, parent_config: Path | str) -> Path:
    p = Path(include_path)
    if p.is_absolute():
        return p
    if str(p).startswith("config/"):
        root_candidate = tenant_root() / p
        if root_candidate.is_file():
            return root_candidate
    parent = Path(parent_config).resolve().parent
    candidate = parent / p
    if candidate.is_file():
        return candidate
    if len(p.parts) == 1:
        sibling = parent / p.name
        if sibling.is_file():
            return sibling
    root_candidate = tenant_root() / p
    if root_candidate.is_file():
        return root_candidate
    return candidate


def load_org_config(path: Path | str) -> dict[str, Any]:
    cfg = load_yaml(path)
    repos: list[dict[str, Any]] = []
    for item in cfg.get("repos") or []:
        if isinstance(item, str):
            repos.append({"name": item, "private": True, "description": ""})
        elif isinstance(item, dict) and item.get("name"):
            repos.append(
                {
                    "name": str(item["name"]),
                    "private": bool(item.get("private", True)),
                    "description": str(item.get("description", "")),
                }
            )
    labels: list[dict[str, str]] = []
    for item in cfg.get("labels") or []:
        if isinstance(item, dict) and item.get("name"):
            labels.append(
                {
                    "name": str(item["name"]),
                    "color": str(item.get("color", "ededed")),
                    "description": str(item.get("description", "")),
                }
            )
    teams: list[dict[str, Any]] = []
    for item in cfg.get("teams") or []:
        if isinstance(item, dict) and item.get("slug"):
            teams.append(
                {
                    "slug": str(item["slug"]),
                    "description": str(item.get("description", "")),
                    "privacy": str(item.get("privacy", "closed")),
                }
            )
    repo_names = [r["name"] for r in repos]
    return {
        "org": cfg.get("org", ""),
        "repos": repos,
        "repo_names": repo_names,
        "labels": labels,
        "teams": teams,
        "path": str(path),
    }


def load_gitflow_config(path: Path | str) -> dict[str, Any]:
    cfg_path = Path(path)
    cfg = load_yaml(cfg_path)
    org_cfg: dict[str, Any] | None = None
    includes = cfg.get("includes") or {}
    if includes.get("org"):
        org_cfg = load_org_config(_resolve_include_path(includes["org"], cfg_path))
    else:
        org_name = str(cfg.get("org", "")).strip()
        if org_name:
            sibling = cfg_path.parent / f"org-{org_name}.yaml"
            if sibling.is_file():
                org_cfg = load_org_config(sibling)

    teams = dict(cfg.get("teams") or {})
    profiles = dict(cfg.get("profiles") or {})
    defaults_raw = dict(cfg.get("defaults") or {})
    default_grant_read = [str(k) for k in (defaults_raw.get("grant_read") or [])]
    default_grant_push = [str(k) for k in (defaults_raw.get("grant_push") or [])]
    repos_raw = cfg.get("repos") or {}
    repos: list[dict[str, Any]] = []
    for name, meta in repos_raw.items():
        if isinstance(meta, dict):
            grant_read = list(
                dict.fromkeys(
                    [
                        *default_grant_read,
                        *[str(k) for k in (meta.get("grant_read") or [])],
                    ]
                )
            )
            grant_push = list(
                dict.fromkeys(
                    [
                        *default_grant_push,
                        *[str(k) for k in (meta.get("grant_push") or [])],
                    ]
                )
            )
            repos.append(
                {
                    "name": str(name),
                    "profile": str(meta.get("profile", "")),
                    "develop_merge": str(meta.get("develop_merge", "")),
                    "grant_read": grant_read,
                    "grant_push": grant_push,
                }
            )
    options = dict(cfg.get("options") or {})
    policy = normalize_gitflow_policy(cfg)
    return {
        "org": cfg.get("org", "") or (org_cfg or {}).get("org", ""),
        "teams": teams,
        "profiles": profiles,
        "repos": repos,
        "repo_names": [r["name"] for r in repos],
        "options": policy["options"],
        "branch_naming": policy["branch_naming"],
        "protection": policy["protection"],
        "merge_policy": policy["merge_policy"],
        "defaults": defaults_raw,
        "org_config": org_cfg,
        "path": str(path),
    }


def load_work_manifest(path: Path | str) -> dict[str, Any]:
    """Load meta WorkManifest (bootstrap / INIT seed-work YAML)."""
    cfg = load_yaml(path)
    kind = cfg.get("kind", "")
    if kind != "WorkManifest":
        raise ValueError(f"expected kind: WorkManifest in {path}, got {kind!r}")
    return {
        "path": str(path),
        "api_version": cfg.get("apiVersion", ""),
        "initiative": cfg.get("initiative", ""),
        "metadata": dict(cfg.get("metadata") or {}),
        "target": dict(cfg.get("target") or {}),
        "defaults": dict(cfg.get("defaults") or {}),
        "epic": dict(cfg.get("epic") or {}) if cfg.get("epic") else None,
        "work": list(cfg.get("work") or []),
    }


def default_project_config_path(org: str) -> Path:
    """Convention: config/project-{org}.yaml"""
    return tenant_config_dir() / f"project-{org}.yaml"


def coerce_yaml_select_option(value: Any) -> str:
    """YAML 1.1 parses yes/no as booleans — coerce to display strings for GitHub Projects."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


_yaml_select_option = coerce_yaml_select_option  # internal alias


def load_project_config(path: Path | str) -> dict[str, Any]:
    cfg_path = Path(path)
    cfg = load_yaml(cfg_path)
    org_cfg: dict[str, Any] | None = None
    includes = cfg.get("includes") or {}
    if includes.get("org"):
        org_cfg = load_org_config(_resolve_include_path(includes["org"], cfg_path))

    fields: list[dict[str, Any]] = []
    for item in cfg.get("fields") or []:
        if not isinstance(item, dict):
            continue
        raw_options = item.get("options") or []
        fields.append(
            {
                "name": item.get("name", ""),
                "type": item.get("type", "TEXT"),
                "options": [coerce_yaml_select_option(o) for o in raw_options],
            }
        )

    issue_types_cfg = cfg.get("issue_types") or {}
    roles_raw = issue_types_cfg.get("roles") or {}
    issue_type_roles = {
        str(k): str(v)
        for k, v in roles_raw.items()
        if k and v
    }
    issue_types_ensure: list[dict[str, Any]] = []
    for item in issue_types_cfg.get("ensure") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        issue_types_ensure.append(
            {
                "name": name,
                "color": str(item.get("color", "gray")),
                "description": str(item.get("description", "")),
            }
        )
    issue_types_required = bool(issue_types_cfg.get("required", bool(issue_types_ensure)))

    repos_raw = cfg.get("repos")
    if repos_raw:
        repos = [str(r) for r in repos_raw]
    elif org_cfg:
        repos = list(org_cfg["repo_names"])
    else:
        repos = []

    return {
        "org": cfg.get("org", "") or (org_cfg or {}).get("org", ""),
        "project_title": cfg.get("project_title", ""),
        "status_columns": list(cfg.get("status_columns") or []),
        "fields": fields,
        "repos": repos,
        "issue_type_roles": issue_type_roles,
        "issue_types_ensure": issue_types_ensure,
        "issue_types_required": issue_types_required,
        "org_config": org_cfg,
        "path": str(path),
    }


def load_platform_manifest(path: Path | str) -> dict[str, Any]:
    cfg = load_yaml(path)
    kind = cfg.get("kind", "")
    if kind != "PlatformManifest":
        raise ValueError(f"expected kind: PlatformManifest in {path}, got {kind!r}")
    setup: list[dict[str, Any]] = []
    for item in cfg.get("setup") or []:
        if isinstance(item, dict):
            setup.append(dict(item))
    verify = dict(cfg.get("verify") or {})
    return {
        "org": cfg.get("org", ""),
        "name": cfg.get("name", ""),
        "setup": setup,
        "verify_config": str(verify.get("config", "")),
        "path": str(path),
    }


def load_verify_manifest(path: Path | str) -> dict[str, Any]:
    cfg_path = Path(path)
    cfg = load_yaml(cfg_path)
    kind = cfg.get("kind", "")
    if kind != "VerifyManifest":
        raise ValueError(f"expected kind: VerifyManifest in {path}, got {kind!r}")

    ctx: dict[str, Any] = {"path": str(path), "org": cfg.get("org", "")}
    includes = cfg.get("includes") or {}
    if includes.get("org"):
        ctx["org_config"] = load_org_config(_resolve_include_path(includes["org"], cfg_path))
    if includes.get("gitflow"):
        ctx["gitflow"] = load_gitflow_config(_resolve_include_path(includes["gitflow"], cfg_path))
    if includes.get("project"):
        ctx["project"] = load_project_config(_resolve_include_path(includes["project"], cfg_path))

    checks: list[dict[str, Any]] = []
    for item in cfg.get("checks") or []:
        if isinstance(item, dict):
            checks.append(dict(item))
    ctx["checks"] = checks
    return ctx


def default_verify_config_path(org: str) -> Path:
    return tenant_config_dir() / f"verify-platform-{org}.yaml"


def default_platform_config_path(org: str) -> Path:
    return tenant_config_dir() / f"platform-{org}.yaml"


def load_harness_config(path: Path | str) -> dict[str, Any]:
    """Load HarnessConfig (rules + skills pins for app repos)."""
    cfg_path = Path(path)
    cfg = load_yaml(cfg_path)
    kind = cfg.get("kind", "")
    if kind != "HarnessConfig":
        raise ValueError(f"expected kind: HarnessConfig in {path}, got {kind!r}")

    profiles: dict[str, Any] = {}
    for name, meta in (cfg.get("profiles") or {}).items():
        if isinstance(meta, dict):
            profiles[str(name)] = dict(meta)

    repos: dict[str, Any] = {}
    for name, meta in (cfg.get("repos") or {}).items():
        if isinstance(meta, dict):
            repos[str(name)] = dict(meta)

    return {
        "org": cfg.get("org", ""),
        "default_workspace": cfg.get("default_workspace", ".."),
        "profiles": profiles,
        "repos": repos,
        "approved_pairs": list(cfg.get("approved_pairs") or []),
        "path": str(path),
    }


def default_harness_config_path(org: str) -> Path:
    return tenant_config_dir() / f"harness-{org}.yaml"


def load_wiki_config(path: Path | str) -> dict[str, Any]:
    """Load WikiConfig (publish-wiki settings)."""
    cfg = load_yaml(path)
    kind = cfg.get("kind", "")
    if kind != "WikiConfig":
        raise ValueError(f"expected kind: WikiConfig in {path}, got {kind!r}")
    return {
        "org": cfg.get("org", ""),
        "repo": cfg.get("repo", ""),
        "wiki_dir": cfg.get("wiki_dir", "wiki"),
        "commit_author_name": cfg.get("commit_author_name", "launchpad"),
        "commit_author_email": cfg.get("commit_author_email", "launchpad@localhost"),
        "commit_message": cfg.get("commit_message", ""),
        "path": str(path),
    }


def default_wiki_config_path(org: str) -> Path:
    return tenant_config_dir() / f"wiki-{org}.yaml"


def default_service_catalog_config_path(org: str) -> Path:
    return tenant_config_dir() / f"service-catalog-{org}.yaml"
