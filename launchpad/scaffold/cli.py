"""CLI wiring for launchpad scaffold commands."""

from __future__ import annotations

import argparse
from pathlib import Path


def _parse_option(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {raw!r}")
    key, _, value = raw.partition("=")
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError(f"empty option key in {raw!r}")
    return key, value.strip()


def parse_scaffold_options(args: argparse.Namespace) -> dict[str, str]:
    return dict(_parse_option(item) for item in args.option)


def _add_scaffold_common_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--template",
        default="",
        help="Cookiecutter template path or gh: URL (default: env or foundation sibling)",
    )
    p.add_argument(
        "--option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override cookiecutter option (repeatable)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="With --apply: overlay foundation into existing tree (preserves product truth)",
    )
    group = p.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True, help="preview only (default)")
    group.add_argument("--apply", action="store_true", help="run cookiecutter")


def add_scaffold_app_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser(
        "scaffold-app",
        help="Generate app repo from a profile cookiecutter (python-backend, …)",
    )
    p.add_argument("--repo", required=True, help="App repo name (e.g. example-api)")
    p.add_argument(
        "--profile",
        default="",
        help="Scaffold profile (default: infer from harness repos.<repo>.profile)",
    )
    p.add_argument("--config", default="", help="HarnessConfig YAML (default: discover harness-*.yaml)")
    p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Parent directory for generated repo (default: harness default_workspace)",
    )
    _add_scaffold_common_flags(p)
    return p


def add_scaffold_meta_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser(
        "scaffold-meta",
        help="Generate or upgrade tenant meta from tenant-meta-foundation cookiecutter",
    )
    p.add_argument(
        "--meta-repo",
        default="",
        help="Meta repo directory name (default: tenant root basename)",
    )
    p.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Meta repo path (default: LAUNCHPAD_TENANT_ROOT)",
    )
    _add_scaffold_common_flags(p)
    return p
