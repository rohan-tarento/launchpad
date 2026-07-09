"""Forge provider registry.

Supported providers in v0.5.10: github
Planned providers: gitlab (v0.6)
"""

from __future__ import annotations

from launchpad.forge.providers.github import GitHubForgeProvider

_PROVIDERS = {
    "github": GitHubForgeProvider,
}

_PLANNED = {
    "gitlab": "v0.6",
}


def get_provider(name: str) -> type:
    """Return the provider class for *name*."""
    if name in _PROVIDERS:
        return _PROVIDERS[name]
    if name in _PLANNED:
        planned_version = _PLANNED[name]
        raise NotImplementedError(
            f"forge provider '{name}' is not yet implemented (planned: {planned_version}). "
            "Only 'github' is supported in v0.5.10."
        )
    raise ValueError(f"Unknown forge provider: '{name}'. Supported: {sorted(_PROVIDERS)}")


__all__ = ["get_provider", "GitHubForgeProvider"]
