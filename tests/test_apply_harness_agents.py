"""Tests for initial AGENTS.md seeding and team-file preservation."""

from __future__ import annotations

from launchpad.commands.apply_harness import _seed_agents_md
from launchpad.schema.harness import HarnessProfile


def _profile(name: str) -> HarnessProfile:
    return HarnessProfile(
        name,
        {"skills": [{"repo": "prayog-skills", "ref": "v0.4.3-rc.1"}]},
    )


def test_seed_agents_creates_initial_meta_guide(tmp_path) -> None:
    _seed_agents_md(
        tmp_path,
        "meta-pm",
        _profile("meta-pm"),
        ["validate-requirements", "prd-impact-map"],
        "sdd-delivery/v2",
        target="example-meta",
        org="example-org",
        meta_repo="example-meta",
        board_name="",
        board_url="",
        apply=True,
    )

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "sdd-delivery/v2" in text
    assert ".agents/skills/<skill>/workflow.yaml" in text
    assert "what next?" in text


def test_seed_agents_preserves_existing_team_file(tmp_path) -> None:
    agents = tmp_path / "AGENTS.md"
    original = "# Team guide\n\nDo not replace this repository-specific context.\n"
    agents.write_text(original, encoding="utf-8")

    _seed_agents_md(
        tmp_path,
        "python-backend",
        _profile("python-backend"),
        ["spec-draft"],
        "sdd-delivery/v2",
        target="example-api",
        org="example-org",
        meta_repo="example-meta",
        board_name="",
        board_url="",
        apply=True,
    )

    assert agents.read_text(encoding="utf-8") == original
