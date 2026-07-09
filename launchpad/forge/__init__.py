"""Forge provider abstraction layer.

v0.5.10 supports GitHub only.
GitLab is a planned provider (v0.6) — the ForgeProvider protocol is already
defined so adding it is a matter of implementing providers/gitlab.py.
"""

from launchpad.forge.protocol import ForgeProvider

__all__ = ["ForgeProvider"]
