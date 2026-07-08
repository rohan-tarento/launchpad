"""Interactive Q&A to build OnboardingSpec."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, TextIO

from launchpad.onboarding.errors import OnboardingError
from launchpad.onboarding.naming import (
    default_meta_repo_name,
    normalize_registry_id,
    validate_registry_id,
)
from launchpad.onboarding.paths import default_spec_path, default_workspace_parent
from launchpad.onboarding.spec import normalize_spec, save_onboarding_spec
from launchpad.platform_repos import DEFAULT_RULES_REF, platform_rules_repo


def _prompt(
    label: str,
    default: str = "",
    *,
    required: bool = False,
    input_fn: Callable[[str], str] | None = None,
    stream: TextIO = sys.stdout,
) -> str:
    reader = input_fn or input
    suffix = f" [{default}]" if default else ""
    while True:
        value = reader(f"{label}{suffix}: ").strip()
        if not value:
            if default:
                return default
            if required:
                stream.write("  (required)\n")
                continue
            return ""
        return value


def _prompt_registry_id(
    label: str,
    default: str = "",
    *,
    field: str = "client_id",
    input_fn: Callable[[str], str] | None = None,
    stream: TextIO = sys.stdout,
) -> str:
    reader = input_fn or input
    while True:
        suffix = f" [{default}]" if default else ""
        value = reader(f"{label}{suffix}: ").strip() or default
        if not value:
            stream.write("  (required)\n")
            continue
        try:
            return validate_registry_id(value, field=field)
        except OnboardingError as exc:
            stream.write(f"  {exc}\n")


def _prompt_yes_no(label: str, default: bool = True, *, input_fn: Callable[[str], str] | None = None) -> bool:
    reader = input_fn or input
    hint = "Y/n" if default else "y/N"
    while True:
        value = reader(f"{label} [{hint}]: ").strip().lower()
        if not value:
            return default
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False


def _parse_repo_suffixes(raw: str, default_profile: str) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    for part in raw.split(","):
        suffix = part.strip().lstrip("-")
        if not suffix:
            continue
        repos.append(
            {
                "suffix": suffix,
                "profile": default_profile,
                "description": suffix,
                "private": True,
            }
        )
    return repos


def build_spec_from_interview(
    *,
    input_fn: Callable[[str], str] | None = None,
    stream: TextIO = sys.stdout,
) -> dict[str, Any]:
    """Collect answers and return normalized OnboardingSpec."""
    reader = input_fn or input
    stream.write("\n=== launchpad onboard interview ===\n\n")
    stream.write(
        "Org vs project: GitHub org (e.g. apex-common) hosts programme repos "
        "(e.g. kola-meta, kola-api).\n"
        "client_id / project_slug are lowercase local names — not the org slug.\n\n"
    )

    project_slug = _prompt_registry_id(
        "Project slug (programme name, lowercase)",
        "kola",
        field="project_slug",
        input_fn=reader,
        stream=stream,
    )
    client_id = _prompt_registry_id(
        "Client id (~/.config/launchpad registry)",
        project_slug,
        field="client_id",
        input_fn=reader,
        stream=stream,
    )
    display_name = _prompt("Display name", project_slug.upper(), input_fn=reader, stream=stream)

    forge_raw = _prompt("Forge type (github/gitlab)", "github", input_fn=reader, stream=stream)
    forge_type = forge_raw.lower()
    if forge_type not in ("github", "gitlab"):
        forge_type = "github"

    org = _prompt(
        "Forge org / group slug (GitHub org — exact spelling, e.g. apex-common)",
        required=True,
        input_fn=reader,
        stream=stream,
    )
    repo_prefix = _prompt_registry_id(
        "Repo prefix (<prefix>-<suffix> repo names)",
        project_slug,
        field="repo_prefix",
        input_fn=reader,
        stream=stream,
    )
    meta_repo = _prompt(
        "Meta repo name",
        default_meta_repo_name(repo_prefix=repo_prefix, project_slug=project_slug),
        input_fn=reader,
        stream=stream,
    )
    workspace = _prompt(
        "Workspace path",
        str(default_workspace_parent()),
        input_fn=reader,
        stream=stream,
    )

    backend_raw = _prompt(
        "Backend repo suffixes (comma-separated; omit prefix — e.g. platform-core,edge-agent)",
        "api",
        input_fn=reader,
        stream=stream,
    )
    repos = _parse_repo_suffixes(backend_raw, "backend")

    frontend_raw = reader(
        "Frontend/BFF repo suffixes (comma-separated, or empty): "
    ).strip()
    if frontend_raw:
        repos.extend(_parse_repo_suffixes(frontend_raw, "frontend"))

    if not repos:
        raise ValueError("at least one app repo is required")

    rules_python_repo = _prompt(
        "Python rules repo (org/name)",
        platform_rules_repo("python"),
        input_fn=reader,
        stream=stream,
    )
    rules_python_ref = _prompt("Python rules initial tag", DEFAULT_RULES_REF, input_fn=reader, stream=stream)

    rules: dict[str, Any] = {
        "python": {"repo": rules_python_repo, "initial_ref": rules_python_ref},
    }
    if any(r["profile"] == "frontend" for r in repos):
        rules["frontend"] = {
            "repo": _prompt(
                "Frontend rules repo (org/name)",
                platform_rules_repo("frontend"),
                input_fn=reader,
                stream=stream,
            ),
            "initial_ref": _prompt("Frontend rules initial tag", DEFAULT_RULES_REF, input_fn=reader, stream=stream),
        }

    strict = _prompt_yes_no("Strict branch naming (INIT/feature/…)?", True, input_fn=reader)
    register = _prompt_yes_no("Register in ~/.config/launchpad/clients.yaml?", True, input_fn=reader)
    set_default = False
    if register:
        set_default = _prompt_yes_no("Set as default client?", False, input_fn=reader)

    raw: dict[str, Any] = {
        "apiVersion": "launchpad/v1",
        "kind": "OnboardingSpec",
        "client_id": client_id,
        "project_slug": project_slug,
        "repo_prefix": repo_prefix,
        "display_name": display_name,
        "forge": {"type": forge_type},
        "org": org,
        "meta_repo": meta_repo,
        "paths": {"workspace": workspace, "spec": "onboarding.yaml"},
        "repos": repos,
        "rules": rules,
        "gitflow": {
            "require_ci": True,
            "branch_naming": True,
            "with_templates": True,
            "branch_naming_mode": "strict" if strict else "standard",
        },
        "project": {"name": f"{display_name} Engineering"},
        "registry": {
            "register_client": register,
            "set_default": set_default,
            "secrets_stub": register,
        },
        "provision": {"run_setup_platform": False, "run_doctor": True},
    }
    return normalize_spec(raw)


def run_interview(*, output: Path | None = None, input_fn: Callable[[str], str] | None = None) -> Path:
    spec = build_spec_from_interview(input_fn=input_fn)
    out = output or default_spec_path()
    save_onboarding_spec(out, spec)
    return out.resolve()
