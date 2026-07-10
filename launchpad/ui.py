"""Terminal UI helpers for launchpad CLI output."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

# Text between side borders: "║  " … " ║"
INNER_WIDTH = 60


def shorten_path(path: str | Path, *, base: Path | None = None) -> str:
    """Display path with ~ for home and optional relative form under *base*."""
    p = Path(path).expanduser()
    try:
        home = Path.home()
        if p.is_relative_to(home):
            rel = p.relative_to(home)
            return "~/" + rel.as_posix()
    except (ValueError, AttributeError, RuntimeError):
        pass

    if base is not None:
        try:
            base_resolved = base.expanduser().resolve()
            resolved = p.resolve()
            if resolved.is_relative_to(base_resolved):
                return resolved.relative_to(base_resolved).as_posix()
        except (ValueError, AttributeError, RuntimeError, OSError):
            pass

    return p.as_posix()


def wrap_next_line(line: str, width: int = INNER_WIDTH) -> list[str]:
    """Wrap a single NEXT hint line, preferring breaks at `` && ``."""
    if len(line) <= width:
        return [line]

    chunks: list[str] = []
    rest = line.strip()
    while rest:
        if len(rest) <= width:
            chunks.append(rest)
            break

        split_at = -1
        for marker in (" && ", " | "):
            idx = rest.rfind(marker, 0, width + 1)
            if idx > 0:
                split_at = idx + len(marker)
                break

        if split_at <= 0:
            idx = rest.rfind(" ", 0, width + 1)
            split_at = idx if idx > 0 else width

        chunk = rest[:split_at].rstrip()
        if chunk:
            chunks.append(chunk)
        rest = rest[split_at:].lstrip()

    return chunks or [line[:width]]


def _body_row(text: str) -> str:
    clipped = text[:INNER_WIDTH]
    return f"║  {clipped:<{INNER_WIDTH}} ║"


def _border() -> str:
    return "═" * (len(_body_row("")) - 2)


def format_next_box(lines: list[str]) -> str:
    """Format a bordered NEXT block with wrapped, width-aligned rows."""
    wrapped: list[str] = []
    for line in lines:
        if not line.strip():
            wrapped.append("")
        else:
            wrapped.extend(wrap_next_line(line.strip()))

    border = _border()
    rows = [
        f"╔{border}╗",
        _body_row("NEXT:"),
        f"╠{border}╣",
    ]
    rows.extend(_body_row(line) for line in wrapped)
    rows.append(f"╚{border}╝")
    return "\n".join(rows)


def print_next_box(lines: list[str], *, file: TextIO | None = None) -> None:
    """Print a blank line and a NEXT box."""
    out = file or sys.stdout
    print(file=out)
    print(format_next_box(lines), file=out)
