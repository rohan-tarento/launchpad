"""Preflight checks for launchpad on a tenant workspace."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from launchpad import __version__
from launchpad.config import discover_tenant_config, load_yaml, tenant_root
from launchpad.forge import forge_from_mapping, gitlab_host_from_mapping
from launchpad.adapters.gitlab.client import GitLabClient, GitLabError
from launchpad.github_client import GitHubClient, GitHubError


def run(*, verbose: bool = False) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    print(f"launchpad {__version__}")
    print("")

    try:
        root = tenant_root()
        print(f"tenant root: {root}")
    except FileNotFoundError as exc:
        print(f"tenant root: NOT FOUND ({exc})")
        errors.append("set LAUNCHPAD_TENANT_ROOT or cd into <client>-meta")
        root = None

    pin = (root / ".launchpad-version").read_text().strip() if root and (root / ".launchpad-version").is_file() else ""
    if pin:
        print(f"pinned launchpad: {pin}")
        if pin != __version__:
            warnings.append(f"installed {__version__} != tenant pin {pin}")
    elif root:
        warnings.append("no .launchpad-version at tenant root")

    forge_type = "github"
    gitlab_host = "https://gitlab.com"
    if root:
        try:
            org_path = discover_tenant_config("org")
            cfg = load_yaml(org_path)
            forge_type = forge_from_mapping(cfg)
            gitlab_host = gitlab_host_from_mapping(cfg)
            print(f"forge: {forge_type}")
        except (FileNotFoundError, ValueError):
            pass

    if forge_type == "gitlab":
        gl_token = os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PRIVATE_TOKEN")
        if gl_token:
            print("GITLAB_TOKEN: set")
            try:
                with GitLabClient(dry_run=False, host=gitlab_host) as client:
                    print(f"gitlab user: {client.whoami()}")
            except GitLabError as exc:
                errors.append(f"gitlab API: {exc}")
        else:
            warnings.append("GITLAB_TOKEN not set (required for gitlab forge)")
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            print("GITHUB_TOKEN: set")
            try:
                with GitHubClient(dry_run=False) as client:
                    login = client.whoami()
                print(f"github user: {login}")
            except GitHubError as exc:
                errors.append(f"github API: {exc}")
        else:
            warnings.append("GITHUB_TOKEN not set (required for github forge)")

    if root:
        for kind in ("platform", "org", "harness"):
            try:
                path = discover_tenant_config(kind)
                print(f"config {kind}: {path.name}")
            except (FileNotFoundError, ValueError) as exc:
                if verbose:
                    print(f"config {kind}: skip ({exc})")
                elif kind == "platform":
                    warnings.append(f"platform config: {exc}")

    print("")
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        return 1
    print("doctor: OK")
    return 0
