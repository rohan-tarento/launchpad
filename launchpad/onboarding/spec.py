"""Load and validate OnboardingSpec YAML."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from launchpad.config import load_yaml
from launchpad.onboarding.errors import OnboardingError

_CLIENT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_REPO_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]+$")
_PROFILES = frozenset({"backend", "frontend", "platform", "data_platform"})
_FORGE_TYPES = frozenset({"github", "gitlab"})
_BRANCH_MODES = frozenset({"standard", "strict"})

DEFAULT_TEAMS = [
    {"slug": "pm-team"},
    {"slug": "backend-devs"},
    {"slug": "frontend-devs"},
    {"slug": "platform-devs"},
    {"slug": "release-managers"},
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


def normalize_spec(raw: dict[str, Any]) -> dict[str, Any]:
    """Apply defaults and return a normalized OnboardingSpec dict."""
    if raw.get("kind") not in (None, "OnboardingSpec"):
        raise OnboardingError(f"expected kind: OnboardingSpec, got {raw.get('kind')!r}")
    if raw.get("apiVersion") not in (None, "launchpad/v1"):
        raise OnboardingError(f"unsupported apiVersion: {raw.get('apiVersion')!r}")

    client_id = str(raw.get("client_id", "")).strip()
    if not _CLIENT_ID_RE.match(client_id):
        raise OnboardingError(
            "client_id must match [a-z][a-z0-9-]{0,62} (e.g. kola)"
        )

    display_name = str(raw.get("display_name") or client_id.upper())
    forge = _require_mapping(raw, "forge") if "forge" in raw else {}
    forge_type = str(forge.get("type") or "github").strip().lower()
    if forge_type not in _FORGE_TYPES:
        raise OnboardingError(f"forge.type must be one of: {', '.join(sorted(_FORGE_TYPES))}")

    org = str(raw.get("org", "")).strip()
    if not org:
        raise OnboardingError("org is required (GitHub/GitLab org slug)")

    meta_repo = str(raw.get("meta_repo") or f"{client_id}-meta").strip()
    if not _REPO_NAME_RE.match(meta_repo):
        raise OnboardingError(f"invalid meta_repo name: {meta_repo!r}")

    paths = _require_mapping(raw, "paths") if "paths" in raw else {}
    workspace = str(paths.get("workspace") or f"~/Workspace/handson/{client_id}").strip()
    spec_name = str(paths.get("spec") or "onboarding.yaml").strip()

    repos_raw = raw.get("repos") or []
    if not isinstance(repos_raw, list) or not repos_raw:
        raise OnboardingError("repos must be a non-empty list of app repos (meta is not listed here)")

    repos: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, item in enumerate(repos_raw):
        if not isinstance(item, dict):
            raise OnboardingError(f"repos[{idx}] must be a mapping")
        name = str(item.get("name", "")).strip()
        if not name:
            raise OnboardingError(f"repos[{idx}].name is required")
        if name == meta_repo:
            raise OnboardingError(f"repos must not include meta repo {meta_repo!r}")
        if name in seen:
            raise OnboardingError(f"duplicate repo name: {name}")
        seen.add(name)
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
            }
        )

    rules_raw = _require_mapping(raw, "rules") if "rules" in raw else {}
    python_rules = _require_mapping(rules_raw, "python") if "python" in rules_raw else {}
    rules_python_repo = str(
        python_rules.get("repo") or f"{org}/python-services-rules"
    ).strip()
    rules_python_ref = str(python_rules.get("initial_ref") or "v0.1.0").strip()

    rules: dict[str, Any] = {
        "python": {"repo": rules_python_repo, "initial_ref": rules_python_ref},
    }
    if "frontend" in rules_raw:
        fe = _require_mapping(rules_raw, "frontend")
        rules["frontend"] = {
            "repo": str(fe.get("repo") or f"{org}/nextjs-bff-rules").strip(),
            "initial_ref": str(fe.get("initial_ref") or "v0.1.0").strip(),
        }
    elif any(r["profile"] == "frontend" for r in repos):
        rules["frontend"] = {
            "repo": f"{org}/nextjs-bff-rules",
            "initial_ref": "v0.1.0",
        }

    agent_skills_raw = _require_mapping(raw, "agent_skills") if "agent_skills" in raw else {}
    agent_skills = {
        "repo": str(agent_skills_raw.get("repo") or "drivestream-lab/prayog-skills").strip(),
        "ref": str(agent_skills_raw.get("ref") or "v0.2.0").strip(),
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
    }

    project_raw = _require_mapping(raw, "project") if "project" in raw else {}
    project = {
        "name": str(project_raw.get("name") or f"{display_name} Engineering").strip(),
        "number": project_raw.get("number"),
    }

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
    raw = load_yaml(path)
    return normalize_spec(raw)


def save_onboarding_spec(path: Path | str, spec: dict[str, Any]) -> None:
    """Write spec to YAML (drops internal _ keys)."""
    out = {k: v for k, v in spec.items() if not str(k).startswith("_")}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(out, f, sort_keys=False, default_flow_style=False)
