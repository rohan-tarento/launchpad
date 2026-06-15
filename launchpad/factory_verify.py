"""Backward-compatible alias for verify.runner."""

from __future__ import annotations

from launchpad.verify.runner import VerifyError as FactoryVerifyError
from launchpad.verify.runner import run, run_applied

__all__ = ["FactoryVerifyError", "run", "run_applied", "verify_scopes", "verify_config_applied"]


def verify_scopes(client, *, org: str, project_config_path: str | None = None) -> None:
    from launchpad.config import default_verify_config_path

    path = project_config_path or str(default_verify_config_path(org))
    run(client, config_path=path, org=org, phase="scopes")


def verify_config_applied(client, *, org: str, project_config_path: str | None = None) -> None:
    from launchpad.config import default_verify_config_path

    path = project_config_path or str(default_verify_config_path(org))
    run_applied(client, config_path=path, org=org)
