"""GitLab forge adapter — STUB (planned: v0.6).

This adapter is preserved for future use.
It is NOT reachable from the v0.5.10 CLI or any public command.
Do not import directly — use launchpad.forge.providers.get_provider("gitlab")
which will raise NotImplementedError with a clear message.
"""

from launchpad.adapters.gitlab.client import GitLabClient, GitLabError

__all__ = ["GitLabClient", "GitLabError"]
