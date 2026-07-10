"""Tests for .gitignore harness seeding during apply-harness."""

from __future__ import annotations

from launchpad.commands.apply_harness import (
    _HARNESS_GITIGNORE_MARKER,
    _harness_gitignore_block,
    _seed_gitignore_harness,
    _upgrade_harness_gitignore_patterns,
)


def test_harness_gitignore_block_has_marker() -> None:
    block = _harness_gitignore_block()
    assert block is not None
    assert _HARNESS_GITIGNORE_MARKER in block
    assert ".agents/skills/*" in block
    assert ".agents/skills/*/" not in block


def test_upgrade_legacy_trailing_slash_patterns() -> None:
    legacy = """.harness/skills/
.agents/skills/*/
.claude/skills/
"""
    upgraded = _upgrade_harness_gitignore_patterns(legacy)
    assert ".agents/skills/*" in upgraded
    assert ".agents/skills/*/" not in upgraded
    assert ".claude/skills/*" in upgraded


def test_seed_gitignore_creates_file(tmp_path) -> None:
    _seed_gitignore_harness(tmp_path, apply=True)
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert _HARNESS_GITIGNORE_MARKER in text
    assert ".harness/skills/" in text


def test_seed_gitignore_appends_to_existing(tmp_path) -> None:
    dest = tmp_path / ".gitignore"
    dest.write_text("*.log\n", encoding="utf-8")
    _seed_gitignore_harness(tmp_path, apply=True)
    text = dest.read_text(encoding="utf-8")
    assert "*.log" in text
    assert _HARNESS_GITIGNORE_MARKER in text


def test_seed_gitignore_upgrades_legacy_without_marker(tmp_path) -> None:
    dest = tmp_path / ".gitignore"
    dest.write_text(
        "# Materialized skill symlinks\n.harness/skills/\n.agents/skills/*/\n.claude/skills/\n",
        encoding="utf-8",
    )
    _seed_gitignore_harness(tmp_path, apply=True)
    text = dest.read_text(encoding="utf-8")
    assert ".agents/skills/*" in text
    assert ".agents/skills/*/" not in text
    assert _HARNESS_GITIGNORE_MARKER not in text


def test_seed_gitignore_idempotent_with_marker(tmp_path) -> None:
    block = _harness_gitignore_block()
    assert block is not None
    (tmp_path / ".gitignore").write_text(block, encoding="utf-8")
    _seed_gitignore_harness(tmp_path, apply=True)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == block
