"""Workspace and spec path defaults for onboarding."""

from __future__ import annotations

from pathlib import Path

DEFAULT_SPEC_FILENAME = "onboarding.yaml"


def default_workspace_parent(
    *,
    spec_dir: Path | str | None = None,
    cwd: Path | str | None = None,
) -> Path:
    """Parent directory for tenant meta + app clones.

    Prefer the onboarding spec's directory, then explicit cwd, then process cwd.
    """
    if spec_dir is not None:
        return Path(spec_dir).expanduser().resolve()
    if cwd is not None:
        return Path(cwd).expanduser().resolve()
    return Path.cwd().resolve()


def default_spec_path(*, cwd: Path | str | None = None) -> Path:
    """Default onboarding.yaml location: current working directory."""
    base = Path(cwd).expanduser().resolve() if cwd is not None else Path.cwd().resolve()
    return base / DEFAULT_SPEC_FILENAME
