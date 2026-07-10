"""Tests for launchpad.ui."""

from __future__ import annotations

from pathlib import Path

from launchpad.ui import (
    INNER_WIDTH,
    format_next_box,
    shorten_path,
    wrap_next_line,
)


def test_wrap_next_line_prefers_and_break() -> None:
    line = "git add .github/ && git commit -m 'chore: forge templates'"
    chunks = wrap_next_line(line, width=40)
    assert len(chunks) >= 2
    assert chunks[0].endswith("&&")
    assert "git commit" in chunks[1]


def test_format_next_box_aligned_borders() -> None:
    long_cmd = (
        "launchpad --client drivestream apply-forge-templates --meta --apply --force"
    )
    box = format_next_box([long_cmd])
    lines = box.splitlines()
    widths = {len(line) for line in lines}
    assert len(widths) == 1
    assert all(line.startswith(("╔", "╠", "╚", "║")) for line in lines)


def test_format_next_box_wraps_without_overflow() -> None:
    line = "cd /Users/me/Workspace/handson/drivestream/drivestream-meta && git add .github/"
    box = format_next_box([line])
    for row in box.splitlines():
        if row.startswith("║"):
            inner = row[3:-2]
            assert len(inner) <= INNER_WIDTH


def test_shorten_path_home() -> None:
    home = shorten_path("~/Workspace/foo")
    assert home.startswith("~/")


def test_shorten_path_relative() -> None:
    base = Path("/tmp/workspace")
    rel = shorten_path("/tmp/workspace/drivestream-meta", base=base)
    assert rel == "drivestream-meta"
