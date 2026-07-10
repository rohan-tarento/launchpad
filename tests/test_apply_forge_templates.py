"""Tests for apply-forge-templates and forge template rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from launchpad.commands.apply_forge_templates import run_apply_forge_templates
from launchpad.forge.templates.render import (
    build_render_context,
    forge_templates_present,
    get_layout,
    render_template,
)
from launchpad.schema.governance import load_governance
from launchpad.schema.programme import load_programme

_CONFIG_DIR = Path(__file__).resolve().parent / "fixtures" / "forge_config"


@pytest.fixture
def forge_config_dir(tmp_path: Path) -> Path:
    cdir = tmp_path / "config"
    cdir.mkdir()
    (cdir / "programme.yaml").write_text(
        ( _CONFIG_DIR / "programme.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (cdir / "governance-example-org.yaml").write_text(
        (_CONFIG_DIR / "governance-example-org.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return cdir


@pytest.fixture
def meta_repo_path(tmp_path: Path, forge_config_dir: Path) -> Path:
    prog = load_programme(forge_config_dir / "programme.yaml")
    repo = tmp_path / prog.meta_repo
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def test_build_render_context_repo_list(forge_config_dir: Path) -> None:
    gov = load_governance(forge_config_dir / "governance-example-org.yaml")
    prog = load_programme(forge_config_dir / "programme.yaml")
    ctx = build_render_context(gov, prog)
    assert "example-api" in ctx["{{REPO_LIST_YAML}}"]
    assert "example-meta" in ctx["{{REPO_LIST_YAML}}"]
    assert ctx["{{ORG}}"] == "example-org"
    assert "example-org" in ctx["{{BOARD_URL}}"]


def test_render_template_substitutions() -> None:
    out = render_template("Org={{ORG}} Meta={{META_REPO}}", {"{{ORG}}": "acme", "{{META_REPO}}": "acme-meta"})
    assert out == "Org=acme Meta=acme-meta"


def test_apply_forge_templates_meta_dry_run(forge_config_dir: Path, meta_repo_path: Path) -> None:
    prog = load_programme(forge_config_dir / "programme.yaml")
    rc = run_apply_forge_templates(
        meta=True,
        apply=False,
        config_dir=forge_config_dir,
        workspace=meta_repo_path.parent,
    )
    assert rc == 0
    assert not (meta_repo_path / ".github/ISSUE_TEMPLATE/feature.yml").is_file()


def test_apply_forge_templates_meta_apply(forge_config_dir: Path, meta_repo_path: Path) -> None:
    prog = load_programme(forge_config_dir / "programme.yaml")
    rc = run_apply_forge_templates(
        meta=True,
        apply=True,
        config_dir=forge_config_dir,
        workspace=meta_repo_path.parent,
    )
    assert rc == 0
    feature = meta_repo_path / ".github/ISSUE_TEMPLATE/feature.yml"
    assert feature.is_file()
    text = feature.read_text(encoding="utf-8")
    assert "example-api" in text
    assert "example-meta" in text
    assert "codebase" in text


def test_apply_forge_templates_app_apply(forge_config_dir: Path, meta_repo_path: Path) -> None:
    app_repo = meta_repo_path.parent / "example-api"
    app_repo.mkdir()
    (app_repo / ".git").mkdir()
    rc = run_apply_forge_templates(
        meta=False,
        repo_name="example-api",
        apply=True,
        config_dir=forge_config_dir,
        workspace=meta_repo_path.parent,
    )
    assert rc == 0
    feature = app_repo / ".github/ISSUE_TEMPLATE/feature.yml"
    assert feature.is_file()
    assert "codebase" not in feature.read_text(encoding="utf-8")


def test_apply_forge_templates_skip_existing(forge_config_dir: Path, meta_repo_path: Path) -> None:
    run_apply_forge_templates(
        meta=True,
        apply=True,
        config_dir=forge_config_dir,
        workspace=meta_repo_path.parent,
    )
    feature = meta_repo_path / ".github/ISSUE_TEMPLATE/feature.yml"
    feature.write_text("# frozen\n", encoding="utf-8")
    rc = run_apply_forge_templates(
        meta=True,
        apply=True,
        config_dir=forge_config_dir,
        workspace=meta_repo_path.parent,
    )
    assert rc == 0
    assert feature.read_text(encoding="utf-8") == "# frozen\n"


def test_apply_forge_templates_force_overwrite(forge_config_dir: Path, meta_repo_path: Path) -> None:
    run_apply_forge_templates(
        meta=True,
        apply=True,
        config_dir=forge_config_dir,
        workspace=meta_repo_path.parent,
    )
    feature = meta_repo_path / ".github/ISSUE_TEMPLATE/feature.yml"
    feature.write_text("# stale\n", encoding="utf-8")
    rc = run_apply_forge_templates(
        meta=True,
        apply=True,
        force=True,
        config_dir=forge_config_dir,
        workspace=meta_repo_path.parent,
    )
    assert rc == 0
    assert "# stale" not in feature.read_text(encoding="utf-8")
    assert "example-api" in feature.read_text(encoding="utf-8")


def test_forge_templates_present_meta(forge_config_dir: Path, meta_repo_path: Path) -> None:
    entries = get_layout("github", is_meta=True)
    assert not forge_templates_present(meta_repo_path, entries)
    run_apply_forge_templates(
        meta=True,
        apply=True,
        config_dir=forge_config_dir,
        workspace=meta_repo_path.parent,
    )
    assert forge_templates_present(meta_repo_path, entries)


def test_gitlab_layout_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        get_layout("gitlab", is_meta=True)
