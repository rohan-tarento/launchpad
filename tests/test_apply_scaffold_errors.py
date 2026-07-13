"""Tests for apply-scaffold operator-facing template errors."""

from __future__ import annotations

from launchpad.commands.apply_scaffold import _parse_cookiecutter_output


SAMPLE_HOOK_OUTPUT = """
ERROR: state storage account name 'stratumstratumtfstatestage' exceeds 24 chars — shorten org_prefix/client, or adjust naming in bootstrap + backend.tf together.
Stopping generation because post_gen_project hook script didn't exit successfully
Traceback (most recent call last):
  File "/Users/me/.local/pipx/venvs/launchpad/lib/python3.14/site-packages/cookiecutter/hooks.py", line 165, in run_hook_from_repo_dir
    run_hook(hook_name, project_dir, context)
cookiecutter.exceptions.FailedHookException: Hook script failed (exit status: 1)
"""


def test_parse_cookiecutter_output_extracts_hook_message():
    messages = _parse_cookiecutter_output(SAMPLE_HOOK_OUTPUT)
    assert len(messages) >= 2
    assert "exceeds 24 chars" in messages[0]
    assert "Stopping generation because" in messages[1]


def test_parse_cookiecutter_output_stops_at_traceback():
    messages = _parse_cookiecutter_output(SAMPLE_HOOK_OUTPUT)
    assert not any("Traceback" in m for m in messages)
    assert not any("FailedHookException" in m for m in messages)


def test_parse_cookiecutter_output_empty():
    assert _parse_cookiecutter_output("") == []
