"""Tests: env.d/<client>.env is SSOT for factory secrets."""

from __future__ import annotations

from pathlib import Path

import pytest

from launchpad import clients as clients_mod


def test_load_client_env_overrides_ambient_github_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_d = tmp_path / "env.d"
    env_d.mkdir()
    (env_d / "drivestream.env").write_text(
        "GITHUB_TOKEN=github_pat_FROM_ENV_D\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(clients_mod, "ENV_D_DIR", env_d)
    monkeypatch.setenv("GITHUB_TOKEN", "github_pat_STALE_SHELL")
    monkeypatch.setenv("GH_TOKEN", "gho_STALE_GH")

    loaded = clients_mod.load_client_env("drivestream")

    assert loaded == env_d / "drivestream.env"
    assert clients_mod.os.environ["GITHUB_TOKEN"] == "github_pat_FROM_ENV_D"


def test_load_client_env_export_prefix_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_d = tmp_path / "env.d"
    env_d.mkdir()
    (env_d / "drivestream.env").write_text(
        "export GITHUB_TOKEN=github_pat_EXPORT_STYLE\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(clients_mod, "ENV_D_DIR", env_d)
    monkeypatch.setenv("GITHUB_TOKEN", "stale")

    clients_mod.load_client_env("drivestream")

    assert clients_mod.os.environ["GITHUB_TOKEN"] == "github_pat_EXPORT_STYLE"
