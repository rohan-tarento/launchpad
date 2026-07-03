"""YAML-driven platform setup — orchestrates bootstrap commands + verify."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from launchpad import bootstrap_org, bootstrap_teams, gitflow, project
from launchpad.config import load_platform_manifest, resolve_config_path
from launchpad.github_client import GitHubClient
from launchpad.verify.runner import VerifyError, run as run_verify


def _resolve_step_config(step: dict[str, Any], manifest_path: Path) -> str:
    raw = step.get("config", "")
    if not raw:
        raise ValueError(f"setup step {step.get('id')!r} missing config path")
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    for base in (manifest_path.parent, manifest_path.parent.parent.parent):
        candidate = base / p
        if candidate.is_file():
            return str(candidate.resolve())
    return str(p)


def _run_step(client: GitHubClient, step: dict[str, Any], *, org: str, platform_path: Path) -> None:
    command = step.get("command", "")
    step_id = step.get("id", command)
    cfg = _resolve_step_config(step, platform_path) if step.get("config") else None

    print(f"=== platform step: {step_id} ({command}) ===")
    if cfg:
        print(f"Config: {cfg}")
    print("")

    if command == "bootstrap-org":
        bootstrap_org.run(client, org=org, config_path=cfg)
    elif command == "bootstrap-teams":
        bootstrap_teams.run(client, org=org, config_path=cfg)
    elif command == "setup-gitflow":
        gitflow.run(
            client,
            org=org,
            config_path=cfg,
            filter_repo=str(step.get("repo") or ""),
        )
    elif command == "bootstrap-project":
        project.run(client, org=org, config_path=cfg)
    else:
        raise ValueError(f"unknown setup command: {command!r}")
    print("")


def run(
    client: GitHubClient,
    *,
    config_path: str | None = None,
    org: str = "",
) -> None:
    platform_path = resolve_config_path("platform", org=org, explicit=config_path)
    manifest = load_platform_manifest(platform_path)
    org = org or manifest["org"]
    verify_config = manifest.get("verify_config", "")
    if verify_config and not Path(verify_config).is_absolute():
        candidate = platform_path.parent / verify_config
        if candidate.is_file():
            verify_config = str(candidate.resolve())

    print("=== setup-platform ===")
    print(f"Manifest: {platform_path}")
    print(f"Name: {manifest.get('name', '')}")
    print(f"Org: {org}")
    print(f"Authenticated as: {client.whoami()}")
    print(f"Mode: {'dry-run' if client.dry_run else 'apply'}")
    print("")

    if not org:
        raise ValueError("org is required in PlatformManifest")
    if not verify_config:
        raise ValueError("verify.config is required in PlatformManifest")

    if not client.dry_run:
        run_verify(client, config_path=verify_config, org=org, phase="scopes")
        print("")

    for step in manifest["setup"]:
        _run_step(client, step, org=org, platform_path=platform_path)

    if client.dry_run:
        print("=== Done (dry-run) ===")
        print("Re-run with --apply to execute setup + verify.")
        print("")
        print("Reminder: <client>-meta is pushed manually before gitflow can configure develop.")
        print("          App repos start empty — scaffold or push main before gitflow step fully applies.")
        return

    print("")
    run_verify(client, config_path=verify_config, org=org, phase="applied")
    print("")
    print("=== Platform ready for backlog ===")
    print("Create or choose a WorkManifest, then:")
    print("  launchpad seed-work --config <work-manifest.yaml> --apply")
