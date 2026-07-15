"""Render kit forge templates with governance / programme substitutions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from launchpad.forge.templates import github as github_layout
from launchpad.forge.templates import gitlab as gitlab_layout
from launchpad.schema.governance import GovernanceSchema
from launchpad.schema.programme import ProgrammeSchema

ForgeTemplateEntry = github_layout.ForgeTemplateEntry


def kit_templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "templates"


def get_layout(provider: str, *, is_meta: bool) -> tuple[ForgeTemplateEntry, ...]:
    if provider == github_layout.PROVIDER:
        return github_layout.entries(is_meta=is_meta)
    if provider == gitlab_layout.PROVIDER:
        return gitlab_layout.entries(is_meta=is_meta)
    raise ValueError(
        f"Unknown forge provider: {provider!r}. Supported: {github_layout.PROVIDER!r}"
    )


def build_render_context(
    gov: GovernanceSchema,
    prog: ProgrammeSchema,
) -> dict[str, str]:
    org = gov.org
    meta_repo = prog.meta_repo
    pb = gov.project_board or {}
    board_name = str(pb.get("name") or "Engineering board")
    board_enabled = bool(pb.get("enabled"))
    number_raw = pb.get("number")
    board_number = int(number_raw) if number_raw is not None and str(number_raw).strip() else None
    board_url = str(pb.get("url") or "").strip()
    if not board_url and board_number is not None:
        board_url = f"https://github.com/orgs/{org}/projects/{board_number}"
    elif board_enabled and not board_url:
        board_url = f"https://github.com/orgs/{org}/projects/1"

    policy = gov.policy or {}
    integration_branch = str(
        policy.get("integration_branch") or policy.get("default_branch") or "develop"
    ).strip()

    playbook_url = (
        f"https://github.com/{org}/{meta_repo}/blob/{integration_branch}/playbook/README.md"
    )
    repo_list_yaml = "\n".join(f"        - {name}" for name in sorted(gov.repos.keys()))

    return {
        "{{ORG}}": org,
        "{{META_REPO}}": meta_repo,
        "{{BOARD_NAME}}": board_name,
        "{{BOARD_URL}}": board_url,
        "{{REPO_LIST_YAML}}": repo_list_yaml,
        "{{PLAYBOOK_URL}}": playbook_url,
        "<client>-meta": meta_repo,
        "example-org": org,
        "example-meta": meta_repo,
        "YOUR_ORG": org,
        "YOUR_META_REPO": meta_repo,
    }


def render_template(content: str, context: dict[str, str]) -> str:
    rendered = content
    for key, value in context.items():
        rendered = rendered.replace(key, value)
    return rendered


def forge_templates_present(repo_path: Path, entries: tuple[ForgeTemplateEntry, ...]) -> bool:
    return all((repo_path / entry.dest_rel).is_file() for entry in entries)
