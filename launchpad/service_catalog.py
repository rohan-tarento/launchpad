"""Service catalog — map repos to teams, branch codes, and capability metadata."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from launchpad.config import discover_tenant_config, load_gitflow_config, load_yaml, tenant_root
from launchpad.github_ops import team_slug_from_config

_PROFILE_TEAM = {
    "backend": "backend-devs",
    "frontend": "frontend-devs",
    "platform": "platform-devs",
    "data_platform": "data-platform-devs",
}

_BRANCH_CODE_RE = re.compile(r"^[A-Z]{2,7}$")


class ServiceCatalogError(RuntimeError):
    """Service catalog could not be loaded or written."""


def suggest_branch_code(repo_name: str, *, meta_repo: str = "") -> str:
    """Suggest a branch_code — review in config/service-catalog-<org>.yaml after generate."""
    if repo_name == meta_repo or repo_name.endswith("-meta"):
        return "META"
    parts = [p for p in repo_name.split("-") if p]
    token = parts[0] if parts else repo_name
    if len(parts) >= 2 and len(parts[0]) <= 4:
        token = parts[-1]
    code = re.sub(r"[^A-Za-z0-9]", "", token).upper()
    if len(code) < 2:
        code = re.sub(r"[^A-Za-z0-9]", "", repo_name).upper()
    return code[:7]


def team_for_profile(profile: str, teams: dict[str, str] | None = None) -> str:
    if teams:
        try:
            return team_slug_from_config(teams, profile)
        except ValueError:
            pass
    return _PROFILE_TEAM.get(profile, "backend-devs")


def _service_entry(
    *,
    name: str,
    org: str,
    profile: str,
    description: str = "",
    branch_code: str = "",
    owns: list[str] | None = None,
    depends_on: list[str] | None = None,
    meta_repo: str = "",
    teams: dict[str, str] | None = None,
) -> dict[str, Any]:
    code = branch_code.strip().upper() if branch_code else suggest_branch_code(name, meta_repo=meta_repo)
    if not _BRANCH_CODE_RE.match(code):
        raise ServiceCatalogError(f"invalid branch_code for {name!r}: {code!r} (need 2-7 uppercase letters)")
    desc = description.strip() or f"{name} — update description in service-catalog-<org>.yaml"
    return {
        "name": name,
        "repo": f"{org}/{name}",
        "team": team_for_profile(profile, teams),
        "branch_code": code,
        "description": desc,
        "owns": list(owns or []),
        "depends_on": list(depends_on or []),
    }


def entries_from_onboarding_spec(spec: dict[str, Any]) -> list[dict[str, Any]]:
    org = str(spec["org"])
    meta_repo = str(spec["meta_repo"])
    services: list[dict[str, Any]] = []

    services.append(
        _service_entry(
            name=meta_repo,
            org=org,
            profile="platform",
            description=(
                f"Tenant meta for {spec.get('display_name', org)} — PRDs, work manifests, "
                "factory config, and playbook."
            ),
            branch_code="META",
            owns=["PRD and initiative management", "factory configuration", "platform playbook"],
            depends_on=[],
            meta_repo=meta_repo,
        )
    )

    for repo in spec.get("repos") or []:
        services.append(
            _service_entry(
                name=str(repo["name"]),
                org=org,
                profile=str(repo.get("profile") or "backend"),
                description=str(repo.get("description") or ""),
                branch_code=str(repo.get("branch_code") or ""),
                owns=[str(x) for x in (repo.get("owns") or [])],
                depends_on=[str(x) for x in (repo.get("depends_on") or [])],
                meta_repo=meta_repo,
            )
        )
    return services


def entries_from_gitflow(cfg: dict[str, Any], *, meta_repo: str = "") -> list[dict[str, Any]]:
    org = str(cfg.get("org") or "")
    if not org:
        raise ServiceCatalogError("org is required in gitflow config")
    teams = dict(cfg.get("teams") or {})
    app_names = set((cfg.get("org_config") or {}).get("repo_names") or [])
    services: list[dict[str, Any]] = []
    for repo_entry in cfg.get("repos") or []:
        name = str(repo_entry["name"])
        profile = str(repo_entry.get("profile") or "backend")
        is_meta = name not in app_names
        if is_meta:
            services.append(
                _service_entry(
                    name=name,
                    org=org,
                    profile="platform",
                    description=f"Tenant meta ({name}) — PRDs, work manifests, factory config.",
                    branch_code="META",
                    owns=["PRD and initiative management", "factory configuration"],
                    depends_on=[],
                    meta_repo=meta_repo or name,
                    teams=teams,
                )
            )
        else:
            services.append(
                _service_entry(
                    name=name,
                    org=org,
                    profile=profile,
                    meta_repo=meta_repo or name,
                    teams=teams,
                )
            )
    return services


def merge_service_entries(
    existing: list[dict[str, Any]],
    desired: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge by service name — preserve curated owns/depends_on/description/branch_code."""
    by_name = {str(s["name"]): dict(s) for s in existing}
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()

    for entry in desired:
        name = str(entry["name"])
        seen.add(name)
        if name in by_name:
            cur = by_name[name]
            merged.append(
                {
                    "name": name,
                    "repo": entry.get("repo") or cur.get("repo"),
                    "team": entry.get("team") or cur.get("team"),
                    "branch_code": cur.get("branch_code") or entry.get("branch_code"),
                    "description": cur.get("description") or entry.get("description"),
                    "owns": cur.get("owns") or entry.get("owns") or [],
                    "depends_on": cur.get("depends_on") or entry.get("depends_on") or [],
                }
            )
        else:
            merged.append(dict(entry))

    for name, cur in by_name.items():
        if name not in seen:
            merged.append(cur)

    merged.sort(key=lambda s: (0 if str(s["name"]).endswith("-meta") else 1, str(s["name"])))
    return merged


def render_service_catalog(*, org: str, services: list[dict[str, Any]]) -> str:
    header = (
        "# Service catalog — maintained by launchpad (sync-catalog / onboard apply)\n"
        "#\n"
        "# Used by PM/dev skills (e.g. /prd-impact-map) and strict branch naming.\n"
        "# branch_code is the {COMPONENT} in feature/INIT-{COMPONENT}-{NUMBER}-{slug}\n"
        "#\n"
        "# Curate owns, depends_on, and descriptions here — sync preserves your edits.\n"
        "# Add new repos via onboarding/scaffold, then: launchpad sync-catalog --apply\n"
    )
    data: dict[str, Any] = {
        "apiVersion": "launchpad/v1",
        "kind": "ServiceCatalog",
        "org": org,
        "services": services,
    }
    body = yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
    return header + body


def load_service_catalog(path: Path | str) -> dict[str, Any]:
    cfg_path = Path(path)
    cfg = load_yaml(cfg_path)
    kind = cfg.get("kind", "")
    if kind != "ServiceCatalog":
        raise ServiceCatalogError(f"expected kind: ServiceCatalog in {cfg_path}, got {kind!r}")
    services: list[dict[str, Any]] = []
    for item in cfg.get("services") or []:
        if isinstance(item, dict) and item.get("name"):
            services.append(dict(item))
    return {
        "org": str(cfg.get("org", "")),
        "services": services,
        "path": str(cfg_path.resolve()),
    }


def resolve_catalog_path(explicit: str | Path | None = None, *, org: str = "") -> Path:
    if explicit:
        p = Path(explicit).expanduser()
        return p.resolve() if p.is_absolute() else (tenant_root() / p).resolve()
    if org:
        return discover_tenant_config("service-catalog", org=org)
    return discover_tenant_config("service-catalog")


def sync_catalog_content(
    *,
    org: str,
    gitflow_path: Path | str,
    existing_path: Path | str | None = None,
    onboarding_spec: dict[str, Any] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    if onboarding_spec:
        desired = entries_from_onboarding_spec(onboarding_spec)
    else:
        gf = load_gitflow_config(gitflow_path)
        org = org or gf["org"]
        meta_candidates = [
            r["name"]
            for r in gf.get("repos") or []
            if r["name"] not in set((gf.get("org_config") or {}).get("repo_names") or [])
        ]
        meta_repo = meta_candidates[0] if len(meta_candidates) == 1 else ""
        desired = entries_from_gitflow(gf, meta_repo=meta_repo)

    catalog_path = resolve_catalog_path(existing_path, org=org)
    existing: list[dict[str, Any]] = []
    if catalog_path.is_file():
        loaded = load_service_catalog(catalog_path)
        if loaded["org"] and loaded["org"] != org:
            raise ServiceCatalogError(
                f"catalog org {loaded['org']!r} != {org!r} — pass --config or fix org field"
            )
        existing = loaded["services"]

    merged = merge_service_entries(existing, desired)
    return render_service_catalog(org=org, services=merged), merged


def run_sync(
    *,
    org: str = "",
    config_path: str | Path | None = None,
    gitflow_path: str | Path | None = None,
    dry_run: bool = True,
) -> None:
    gf_path = Path(gitflow_path) if gitflow_path else tenant_root() / "config" / f"gitflow-{org}.yaml"
    if not gf_path.is_file():
        gf_matches = sorted((tenant_root() / "config").glob("gitflow-*.yaml"))
        if len(gf_matches) == 1:
            gf_path = gf_matches[0]
        elif not gf_path.is_file():
            raise ServiceCatalogError(f"gitflow config not found: {gf_path}")

    gf = load_gitflow_config(gf_path)
    org = org or gf["org"]
    catalog_path = resolve_catalog_path(config_path, org=org)

    print("=== sync-catalog ===")
    print(f"Catalog: {catalog_path}")
    print(f"Gitflow: {gf_path}")
    print(f"Org: {org}")
    print(f"Mode: {'dry-run' if dry_run else 'apply'}")
    print("")

    meta_candidates = [
        r["name"]
        for r in gf.get("repos") or []
        if r["name"] not in set((gf.get("org_config") or {}).get("repo_names") or [])
    ]
    meta_repo = meta_candidates[0] if len(meta_candidates) == 1 else ""
    desired = entries_from_gitflow(gf, meta_repo=meta_repo)
    content, merged = sync_catalog_content(org=org, gitflow_path=gf_path, existing_path=catalog_path)
    print(f"Services: {len(desired)} from gitflow → {len(merged)} in catalog (merge preserves curated fields)")
    for svc in merged:
        print(f"  • {svc['name']} ({svc['branch_code']}) → {svc['team']}")

    if dry_run:
        print("")
        print(f"[dry-run] would write {catalog_path}")
        print("Re-run with --apply to execute.")
        return

    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(content, encoding="utf-8")
    print("")
    print(f"Wrote: {catalog_path}")
    print("Curate owns, depends_on, and descriptions — re-run sync-catalog after adding repos.")
