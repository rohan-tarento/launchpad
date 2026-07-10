"""GitLab forge layout — planned for v0.6."""

from __future__ import annotations

PROVIDER = "gitlab"
PLANNED_VERSION = "v0.6"


def entries(*, is_meta: bool) -> tuple:
    raise NotImplementedError(
        f"forge provider '{PROVIDER}' templates are not yet implemented "
        f"(planned: {PLANNED_VERSION}). Only 'github' is supported."
    )
