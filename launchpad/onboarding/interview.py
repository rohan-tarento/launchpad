"""Interactive Q&A to build OnboardingSpec."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, TextIO

from launchpad.onboarding.spec import normalize_spec, save_onboarding_spec


def _prompt(
    label: str,
    default: str = "",
    *,
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
            stream.write("  (required)\n")
            continue
        return value


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


def _parse_repos(raw: str, default_profile: str) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    for part in raw.split(","):
        name = part.strip()
        if not name:
            continue
        repos.append(
            {
                "name": name,
                "profile": default_profile,
                "description": name,
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

    client_id = _prompt("Client id (registry, e.g. kola)", input_fn=reader, stream=stream)
    display_name = _prompt("Display name", client_id.upper(), input_fn=reader, stream=stream)

    forge_raw = _prompt("Forge type (github/gitlab)", "github", input_fn=reader, stream=stream)
    forge_type = forge_raw.lower()
    if forge_type not in ("github", "gitlab"):
        forge_type = "github"

    org = _prompt("Forge org / group slug", f"{client_id}-lab", input_fn=reader, stream=stream)
    meta_repo = _prompt("Meta repo name", f"{client_id}-meta", input_fn=reader, stream=stream)
    workspace = _prompt("Workspace path", f"~/Workspace/handson/{client_id}", input_fn=reader, stream=stream)

    backend_raw = _prompt(
        "Backend app repos (comma-separated)",
        f"{client_id}-api",
        input_fn=reader,
        stream=stream,
    )
    repos = _parse_repos(backend_raw, "backend")

    frontend_raw = reader("Frontend/BFF repos (comma-separated, or empty): ").strip()
    if frontend_raw:
        repos.extend(_parse_repos(frontend_raw, "frontend"))

    if not repos:
        raise ValueError("at least one app repo is required")

    rules_python_repo = _prompt(
        "Python rules repo (org/name)",
        f"{org}/python-services-rules",
        input_fn=reader,
        stream=stream,
    )
    rules_python_ref = _prompt("Python rules initial tag", "v0.1.0", input_fn=reader, stream=stream)

    rules: dict[str, Any] = {
        "python": {"repo": rules_python_repo, "initial_ref": rules_python_ref},
    }
    if any(r["profile"] == "frontend" for r in repos):
        rules["frontend"] = {
            "repo": _prompt(
                "Frontend rules repo (org/name)",
                f"{org}/nextjs-bff-rules",
                input_fn=reader,
                stream=stream,
            ),
            "initial_ref": _prompt("Frontend rules initial tag", "v0.1.0", input_fn=reader, stream=stream),
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
    workspace = Path(spec["paths"]["workspace"])
    out = output or (workspace / spec["paths"]["spec"])
    save_onboarding_spec(out, spec)
    return out.resolve()
