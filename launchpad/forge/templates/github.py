"""GitHub forge layout — maps kit templates to .github/ paths."""

from __future__ import annotations

from dataclasses import dataclass

PROVIDER = "github"


@dataclass(frozen=True)
class ForgeTemplateEntry:
    kit_name: str
    dest_rel: str


# Meta repo: full forms with Codebase dropdown (kit issues/*.yml).
META_ENTRIES: tuple[ForgeTemplateEntry, ...] = (
    ForgeTemplateEntry("issues/feature.yml", ".github/ISSUE_TEMPLATE/feature.yml"),
    ForgeTemplateEntry("issues/bug.yml", ".github/ISSUE_TEMPLATE/bug.yml"),
    ForgeTemplateEntry("issues/chore.yml", ".github/ISSUE_TEMPLATE/chore.yml"),
    ForgeTemplateEntry("issues/config.yml", ".github/ISSUE_TEMPLATE/config.yml"),
    ForgeTemplateEntry("pull_request_template.md", ".github/pull_request_template.md"),
)

# App repo: no Codebase dropdown (kit issues/*.app.yml).
APP_ENTRIES: tuple[ForgeTemplateEntry, ...] = (
    ForgeTemplateEntry("issues/feature.app.yml", ".github/ISSUE_TEMPLATE/feature.yml"),
    ForgeTemplateEntry("issues/bug.app.yml", ".github/ISSUE_TEMPLATE/bug.yml"),
    ForgeTemplateEntry("issues/chore.app.yml", ".github/ISSUE_TEMPLATE/chore.yml"),
    ForgeTemplateEntry("issues/config.app.yml", ".github/ISSUE_TEMPLATE/config.yml"),
    ForgeTemplateEntry("pull_request_template.md", ".github/pull_request_template.md"),
)


def entries(*, is_meta: bool) -> tuple[ForgeTemplateEntry, ...]:
    return META_ENTRIES if is_meta else APP_ENTRIES
