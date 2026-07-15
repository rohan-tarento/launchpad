"""Tests for programme board binding resolution."""

from __future__ import annotations

from launchpad.harness.skills_resolve import _profile_matches
from launchpad.programme.board_binding import resolve_board_binding


def test_resolve_board_binding_from_number() -> None:
    binding = resolve_board_binding(
        "autrio10x",
        {"enabled": True, "name": "MOBBOT Engineering", "number": 3},
    )
    assert binding.name == "MOBBOT Engineering"
    assert binding.number == 3
    assert binding.url == "https://github.com/orgs/autrio10x/projects/3"


def test_resolve_board_binding_from_url() -> None:
    binding = resolve_board_binding(
        "autrio10x",
        {
            "enabled": True,
            "name": "MOBBOT Engineering",
            "url": "https://github.com/orgs/autrio10x/projects/5",
        },
    )
    assert binding.number == 5


def test_profile_matches_app_token() -> None:
    assert _profile_matches("python-backend", ["app"])
    assert _profile_matches("frontend", ["app"])
    assert _profile_matches("terraform-iac", ["app"])
    assert not _profile_matches("meta-pm", ["app"])
    assert _profile_matches("meta-pm", ["meta-pm"])
