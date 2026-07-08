"""Load and validate OnboardingSpec YAML."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from launchpad.config import load_yaml
from launchpad.onboarding.errors import OnboardingError
from launchpad.onboarding.naming import (
    default_meta_repo_name,
    normalize_registry_id,
    parse_repo_entries,
    resolve_project_slug,
    resolve_repo_prefix,
    validate_registry_id,
)
from launchpad.onboarding.paths import default_workspace_parent
from launchpad.platform_repos import (
    DEFAULT_AGENT_SKILLS_REF,
    DEFAULT_RULES_REF,
    PRAYOG_SKILLS_REPO,
    platform_rules_repo,
)

_REPO_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]+$")
_PROFILES = frozenset({"backend", "frontend", "platform", "data_platform"})
_FORGE_TYPES = frozenset({"github", "gitlab"})
_BRANCH_MODES = frozenset({"standard", "strict"})

DEFAULT_TEAMS = [
    {"slug": "pm-team"},
    {"slug": "backend-devs"},
    {"slug": "frontend-devs"},
    {"slug": "platform-devs"},
    {"slug": "data-platform-devs"},
    {"slug": "release-managers"},
    {"slug": "qa-team"},
    {"slug": "pe-team"},
]

DEFAULT_LABELS = [
    {"name": "initiative", "color": "1E3A8A", "description": "Platform epic / INIT work"},
    {"name": "spec", "color": "0E7490", "description": "Spec handoff PR"},
]


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise OnboardingError(f"{key} must be a mapping")
    return value


def _expand_path(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def org_config_basename(org: str) -> str:
    return f"org-{org}.yaml"


def normalize_spec(
    raw: dict[str, Any],
    *,
    spec_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Apply defaults and return a normalized OnboardingSpec dict."""
    if raw.get("kind") not in (None, "OnboardingSpec"):
        raise OnboardingError(f"expected kind: OnboardingSpec, got {raw.get('kind')!r}")
    if raw.get("apiVersion") not in (None, "launchpad/v1"):
        raise OnboardingError(f"unsupported apiVersion: {raw.get('apiVersion')!r}")

    client_id_raw = str(raw.get("client_id", "")).strip()
    try:
        client_id = validate_registry_id(client_id_raw, field="client_id")
    except OnboardingError:
        if client_id_raw and client_id_raw.lower() != client_id_raw:
            raise OnboardingError(
                f"client_id must be lowercase (got {client_id_raw!r}). "
                "Use your programme slug (e.g. kola) — the GitHub org name "
                "belongs in org:, not client_id."
            ) from None
        raise

    project_slug = resolve_project_slug(raw, client_id=client_id)
    display_name = str(raw.get("display_name") or project_slug.upper())
    forge = _require_mapping(raw, "forge") if "forge" in raw else {}
    forge_type = str(forge.get("type") or "github").strip().lower()
    if forge_type not in _FORGE_TYPES:
        raise OnboardingError(f"forge.type must be one of: {', '.join(sorted(_FORGE_TYPES))}")

    org = str(raw.get("org", "")).strip()
    if not org:
        raise OnboardingError("org is required (GitHub/GitLab org slug)")

    repos_container = raw.get("repos") or []
    repo_prefix = resolve_repo_prefix(raw, project_slug=project_slug, repos_container=repos_container)
    meta_repo = str(
        raw.get("meta_repo") or default_meta_repo_name(repo_prefix=repo_prefix, project_slug=project_slug)
    ).strip()
    if not _REPO_NAME_RE.match(meta_repo):
        raise OnboardingError(f"invalid meta_repo name: {meta_repo!r}")

    paths = _require_mapping(raw, "paths") if "paths" in raw else {}
    workspace_raw = str(paths.get("workspace") or "").strip()
    if workspace_raw:
        workspace = workspace_raw
    else:
        workspace = str(default_workspace_parent(spec_dir=spec_dir))
    spec_name = str(paths.get("spec") or "onboarding.yaml").strip()

    repo_entries = parse_repo_entries(
        repos_container,
        repo_prefix=repo_prefix,
        meta_repo=meta_repo,
    )

    repos: list[dict[str, Any]] = []
    for idx, item in enumerate(repo_entries):
        name = item["name"]
        if not _REPO_NAME_RE.match(name):
            raise OnboardingError(f"invalid repo name: {name!r}")
        profile = str(item.get("profile") or "backend").strip()
        if profile not in _PROFILES:
            raise OnboardingError(
                f"repos[{idx}].profile must be one of: {', '.join(sorted(_PROFILES))}"
            )
        repos.append(
            {
                "name": name,
                "profile": profile,
                "description": str(item.get("description") or name),
                "private": bool(item.get("private", True)),
                "branch_code": str(item.get("branch_code") or "").strip(),
                "owns": [str(x) for x in (item.get("owns") or [])],
                "depends_on": [str(x) for x in (item.get("depends_on") or [])],
            }
        )

    rules_raw = _require_mapping(raw, "rules") if "rules" in raw else {}
    python_rules = _require_mapping(rules_raw, "python") if "python" in rules_raw else {}
    rules_python_repo = str(
        python_rules.get("repo") or platform_rules_repo("python")
    ).strip()
    rules_python_ref = str(python_rules.get("initial_ref") or DEFAULT_RULES_REF).strip()

    rules: dict[str, Any] = {
        "python": {"repo": rules_python_repo, "initial_ref": rules_python_ref},
    }
    if "frontend" in rules_raw:
        fe = _require_mapping(rules_raw, "frontend")
        rules["frontend"] = {
            "repo": str(fe.get("repo") or platform_rules_repo("frontend")).strip(),
            "initial_ref": str(fe.get("initial_ref") or DEFAULT_RULES_REF).strip(),
        }
    elif any(r["profile"] == "frontend" for r in repos):
        rules["frontend"] = {
            "repo": platform_rules_repo("frontend"),
            "initial_ref": DEFAULT_RULES_REF,
        }

    if "data_platform" in rules_raw:
        dp = _require_mapping(rules_raw, "data_platform")
        rules["data_platform"] = {
            "repo": str(dp.get("repo") or platform_rules_repo("data_platform")).strip(),
            "initial_ref": str(dp.get("initial_ref") or DEFAULT_RULES_REF).strip(),
        }
    elif any(r["profile"] == "data_platform" for r in repos):
        rules["data_platform"] = {
            "repo": platform_rules_repo("data_platform"),
            "initial_ref": DEFAULT_RULES_REF,
        }

    agent_skills_raw = _require_mapping(raw, "agent_skills") if "agent_skills" in raw else {}
    agent_skills = {
        "repo": str(agent_skills_raw.get("repo") or PRAYOG_SKILLS_REPO).strip(),
        "ref": str(agent_skills_raw.get("ref") or DEFAULT_AGENT_SKILLS_REF).strip(),
    }

    teams_raw = raw.get("teams")
    teams = DEFAULT_TEAMS if teams_raw is None else teams_raw
    if not isinstance(teams, list) or not teams:
        raise OnboardingError("teams must be a non-empty list")
    norm_teams: list[dict[str, str]] = []
    for idx, team in enumerate(teams):
        if isinstance(team, str):
            norm_teams.append({"slug": team.strip()})
            continue
        if not isinstance(team, dict):
            raise OnboardingError(f"teams[{idx}] must be a string or mapping")
        slug = str(team.get("slug", "")).strip()
        if not slug:
            raise OnboardingError(f"teams[{idx}].slug is required")
        norm_teams.append({"slug": slug})

    gitflow_raw = _require_mapping(raw, "gitflow") if "gitflow" in raw else {}
    branch_mode = str(gitflow_raw.get("branch_naming_mode") or "strict").strip()
    if branch_mode not in _BRANCH_MODES:
        raise OnboardingError("gitflow.branch_naming_mode must be standard or strict")
    gitflow = {
        "require_ci": bool(gitflow_raw.get("require_ci", True)),
        "branch_naming": bool(gitflow_raw.get("branch_naming", True)),
        "with_templates": bool(gitflow_raw.get("with_templates", True)),
        "branch_naming_mode": branch_mode,
        "set_default_branch": bool(gitflow_raw.get("set_default_branch", True)),
    }

    project_raw = _require_mapping(raw, "project") if "project" in raw else {}
    project: dict[str, Any] = {
        "name": str(project_raw.get("name") or f"{display_name} Engineering").strip(),
        "number": project_raw.get("number"),
    }
    issue_types_raw = project_raw.get("issue_types")
    if isinstance(issue_types_raw, dict):
        project["issue_types"] = issue_types_raw
    team_access_raw = project_raw.get("team_access")
    if team_access_raw is not None:
        project["team_access"] = team_access_raw

    overrides_raw = _require_mapping(raw, "overrides") if "overrides" in raw else {}
    overrides = {
        "generate_templates": bool(overrides_raw.get("generate_templates", True)),
        "generate_playbook_hub": bool(overrides_raw.get("generate_playbook_hub", True)),
        "board_url": str(overrides_raw.get("board_url") or "").strip(),
    }

    registry_raw = _require_mapping(raw, "registry") if "registry" in raw else {}
    registry = {
        "register_client": bool(registry_raw.get("register_client", True)),
        "set_default": bool(registry_raw.get("set_default", False)),
        "secrets_stub": bool(registry_raw.get("secrets_stub", True)),
    }

    provision_raw = _require_mapping(raw, "provision") if "provision" in raw else {}
    provision = {
        "run_setup_platform": bool(provision_raw.get("run_setup_platform", False)),
        "run_doctor": bool(provision_raw.get("run_doctor", True)),
    }

    workspace_path = _expand_path(workspace)
    meta_path = workspace_path / meta_repo

    return {
        "apiVersion": "launchpad/v1",
        "kind": "OnboardingSpec",
        "client_id": client_id,
        "project_slug": project_slug,
        "repo_prefix": repo_prefix,
        "display_name": display_name,
        "forge": {"type": forge_type},
        "org": org,
        "meta_repo": meta_repo,
        "paths": {
            "workspace": str(workspace_path),
            "spec": spec_name,
        },
        "repos": repos,
        "rules": rules,
        "agent_skills": agent_skills,
        "teams": norm_teams,
        "labels": raw.get("labels") or DEFAULT_LABELS,
        "gitflow": gitflow,
        "project": project,
        "overrides": overrides,
        "registry": registry,
        "provision": provision,
        "_meta_path": str(meta_path),
        "_org_config": org_config_basename(org),
    }


def load_onboarding_spec(path: Path | str) -> dict[str, Any]:
    spec_path = Path(path).expanduser().resolve()
    raw = load_yaml(spec_path)
    return normalize_spec(raw, spec_dir=spec_path.parent)


def save_onboarding_spec(path: Path | str, spec: dict[str, Any]) -> None:
    """Write spec to YAML (drops internal _ keys)."""
    out = {k: v for k, v in spec.items() if not str(k).startswith("_")}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(out, f, sort_keys=False, default_flow_style=False)
