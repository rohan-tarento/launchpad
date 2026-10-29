"""Tests for delivery workflow seeding during apply-harness."""

from __future__ import annotations

import yaml

from launchpad.commands.apply_harness import (
    _DELIVERY_WORKFLOW_TEMPLATES,
    _seed_delivery_workflows,
)
from launchpad.harness.paths import PM_HARNESS_PROFILE


def test_seed_delivery_workflows_creates_files(tmp_path) -> None:
    _seed_delivery_workflows(
        tmp_path,
        delivery_contract="sdd-delivery/v2",
        profile_name="python-backend",
        apply=True,
    )
    workflows = tmp_path / ".github" / "workflows"
    for kit_rel in _DELIVERY_WORKFLOW_TEMPLATES:
        assert (workflows / kit_rel.split("/")[-1]).is_file()

    # BaseLoader preserves the YAML key "on" as a string.
    ci = yaml.load((workflows / "ci.yml").read_text(), Loader=yaml.BaseLoader)
    assert ci["on"] == {"pull_request": {"branches": ["main"]}}
    policy = yaml.load(
        (workflows / "policy-branch-name.yml").read_text(), Loader=yaml.BaseLoader
    )
    assert policy["on"] == {"pull_request": {"branches": ["develop"]}}
    assert not (workflows / "board-seed-gate.yml").exists()


def test_seed_delivery_workflows_skips_meta_pm(tmp_path) -> None:
    _seed_delivery_workflows(
        tmp_path,
        delivery_contract="sdd-delivery/v2",
        profile_name=PM_HARNESS_PROFILE,
        apply=True,
    )
    assert not (tmp_path / ".github").exists()


def test_seed_delivery_workflows_skips_without_contract(tmp_path) -> None:
    _seed_delivery_workflows(
        tmp_path,
        delivery_contract="",
        profile_name="python-backend",
        apply=True,
    )
    assert not (tmp_path / ".github").exists()


def test_seed_delivery_workflows_idempotent(tmp_path) -> None:
    _seed_delivery_workflows(
        tmp_path,
        delivery_contract="sdd-delivery/v2",
        profile_name="python-backend",
        apply=True,
    )
    workflows = tmp_path / ".github" / "workflows"
    first_ci = (workflows / "ci.yml").read_text(encoding="utf-8")
    _seed_delivery_workflows(
        tmp_path,
        delivery_contract="sdd-delivery/v2",
        profile_name="python-backend",
        apply=True,
    )
    assert (workflows / "ci.yml").read_text(encoding="utf-8") == first_ci
