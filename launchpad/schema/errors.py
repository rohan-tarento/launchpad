"""Schema validation errors."""

from __future__ import annotations


class SchemaError(Exception):
    """Raised when a YAML config file fails schema validation.

    Includes the file path and a human-readable fix hint wherever possible.
    """

    def __init__(self, message: str, *, path: str = "", hint: str = "") -> None:
        self.path = path
        self.hint = hint
        detail = f" ({path})" if path else ""
        fix = f"\n  Fix: {hint}" if hint else ""
        super().__init__(f"{message}{detail}{fix}")
