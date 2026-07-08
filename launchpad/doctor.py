"""Preflight checks for launchpad on a tenant workspace (v0.5.10).

Checks:
  • LAUNCHPAD_CLIENT / clients.yaml lookup
  • programme.yaml exists and is valid
  • programme_slug matches clients.yaml id
  • GITHUB_TOKEN is set and not a placeholder
  • GitHub API reachable and token valid
  • .launchpad-version matches installed version
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from launchpad import __version__
from launchpad.clients import ENV_D_DIR
from launchpad.github_client import GitHubClient, GitHubError


_TOKEN_PLACEHOLDER = "github_pat_REPLACE_ME"


def run(*, verbose: bool = False) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    print(f"launchpad {__version__}")
    print()

    # ── Client context ──────────────────────────────────────────────────────
    client_id = os.environ.get("LAUNCHPAD_CLIENT", "").strip()
    if client_id:
        env_file = ENV_D_DIR / f"{client_id}.env"
        print(f"client:  {client_id}")
        if env_file.is_file():
            print(f"secrets: {env_file}")
        else:
            warnings.append(f"env file not found: {env_file}  (run onboard interview)")

    # ── Tenant root / programme.yaml ────────────────────────────────────────
    tenant_root: Path | None = None
    try:
        from launchpad.config import tenant_root as _tenant_root
        tenant_root = _tenant_root()
        print(f"meta:    {tenant_root}")
    except FileNotFoundError:
        warnings.append(
            "meta repo root not found — "
            "set LAUNCHPAD_TENANT_ROOT, use --client <id>, or cd into <slug>-meta"
        )

    programme_slug_from_yaml: str = ""
    if tenant_root:
        prog_path = tenant_root / "config" / "programme.yaml"
        if prog_path.is_file():
            try:
                from launchpad.schema.programme import load_programme
                prog = load_programme(prog_path)
                programme_slug_from_yaml = prog.programme_slug
                print(f"programme: {prog.programme}  (slug: {prog.programme_slug}  org: {prog.org})")

                # Cross-check slug vs clients.yaml id
                if client_id and programme_slug_from_yaml and client_id != programme_slug_from_yaml:
                    warnings.append(
                        f"LAUNCHPAD_CLIENT='{client_id}' does not match "
                        f"programme_slug='{programme_slug_from_yaml}' in programme.yaml"
                    )
            except Exception as exc:
                warnings.append(f"programme.yaml invalid: {exc}")
        elif verbose:
            print("programme.yaml: not found (run onboard interview)")

        pin_path = tenant_root / ".launchpad-version"
        if pin_path.is_file():
            pin = pin_path.read_text().strip()
            print(f"pinned:  {pin}")
            if pin != __version__:
                warnings.append(f"installed {__version__} != .launchpad-version pin {pin}")
        else:
            warnings.append("no .launchpad-version at meta root")

    # ── GitHub token ────────────────────────────────────────────────────────
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not token:
        env_hint = f"env.d/{client_id or '<slug>'}.env" if client_id else "env.d/<slug>.env"
        errors.append(
            f"GITHUB_TOKEN not set — "
            f"add it to {ENV_D_DIR / (client_id or '<slug>') }.env and source it"
        )
    elif token == _TOKEN_PLACEHOLDER:
        env_file_path = ENV_D_DIR / f"{client_id or 'unknown'}.env"
        errors.append(
            f"GITHUB_TOKEN is still the placeholder — "
            f"replace it in {env_file_path}"
        )
    else:
        print("GITHUB_TOKEN: set")
        try:
            with GitHubClient(dry_run=False) as client:
                login = client.whoami()
            print(f"github user: {login}")
        except GitHubError as exc:
            errors.append(f"GitHub API error: {exc}")

    print()
    for w in warnings:
        print(f"WARN:  {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        return 1

    print("doctor: OK")
    return 0
