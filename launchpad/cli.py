"""CLI entry point for launchpad (v0.5.10).

Public commands:
  onboard interview   4-question setup → writes 5 config YAMLs locally
  init-client         Day-1 / Day-N GitHub setup (teams, repos, gitflow, board)
  apply-scaffold      Cookiecutter scaffold from scaffold-<org>.yaml
  apply-harness       Pin constitution + seed agent skills from harness-<org>.yaml
  check-harness       Verify harness pins and submodule state
  doctor              Preflight: token, config, version checks
  clients             List registered clients (~/.config/launchpad/clients.yaml)
  whoami              Verify GITHUB_TOKEN and print login

All apply commands are dry-run by default — pass --apply to execute.
All commands require --meta OR --repo <name> (no --all flag).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from launchpad import __version__
from launchpad.clients import ClientRegistryError, apply_client_context, format_clients_table
from launchpad.doctor import run as run_doctor
from launchpad.github_client import GitHubClient, GitHubError
from launchpad.onboarding.cli import add_onboard_parser
from launchpad.onboarding.errors import OnboardingError
from launchpad.schema.errors import SchemaError


def _add_apply_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True, help="print actions only (default)")
    group.add_argument("--apply", action="store_true", help="execute against GitHub API")


def _add_scope_flags(parser: argparse.ArgumentParser) -> None:
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--meta", action="store_true", help="target the meta repo")
    scope.add_argument("--repo", default="", metavar="NAME", help="target a specific app repo")


def _dry_run_from_args(args: argparse.Namespace) -> bool:
    return not getattr(args, "apply", False)


def _config_dir(args: argparse.Namespace) -> Path | None:
    raw = getattr(args, "config_dir", "") or ""
    return Path(raw).expanduser().resolve() if raw else None


# ── Command handlers ──────────────────────────────────────────────────────────


def cmd_doctor(args: argparse.Namespace) -> int:
    return run_doctor(verbose=args.verbose)


def cmd_clients(args: argparse.Namespace) -> int:
    print(format_clients_table())
    return 0


def cmd_whoami(args: argparse.Namespace) -> int:
    with GitHubClient(dry_run=False) as client:
        print(client.whoami())
    return 0


def cmd_init_client(args: argparse.Namespace) -> int:
    from launchpad.commands.init_client import run_init_client

    return run_init_client(
        meta=args.meta,
        repo_name=args.repo or "",
        apply=getattr(args, "apply", False),
        dry_run=_dry_run_from_args(args),
        config_dir=_config_dir(args),
    )


def cmd_apply_scaffold(args: argparse.Namespace) -> int:
    from launchpad.commands.apply_scaffold import run_apply_scaffold

    return run_apply_scaffold(
        meta=args.meta,
        repo_name=args.repo or "",
        apply=getattr(args, "apply", False),
        force=getattr(args, "force", False),
        config_dir=_config_dir(args),
    )


def cmd_apply_harness(args: argparse.Namespace) -> int:
    from launchpad.commands.apply_harness import run_apply_harness

    return run_apply_harness(
        meta=args.meta,
        repo_name=args.repo or "",
        apply=getattr(args, "apply", False),
        config_dir=_config_dir(args),
    )


def cmd_check_harness(args: argparse.Namespace) -> int:
    from launchpad.commands.check_harness import run_check_harness

    return run_check_harness(
        meta=args.meta,
        repo_name=args.repo or "",
        config_dir=_config_dir(args),
    )


def cmd_status(args: argparse.Namespace) -> int:
    from launchpad.commands.status import run_status

    return run_status(
        meta=args.meta,
        repo_name=args.repo or "",
        config_dir=_config_dir(args),
    )


# ── Parser ────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="launchpad",
        description=(
            "Launchpad factory automation (v0.5.10 · GitHub only).\n"
            "Run from your <slug>-meta workspace, or use --client.\n"
            "All commands are dry-run by default — pass --apply to execute."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--client",
        default=os.environ.get("LAUNCHPAD_CLIENT", ""),
        metavar="ID",
        help="client id from ~/.config/launchpad/clients.yaml (or LAUNCHPAD_CLIENT env)",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── doctor ────────────────────────────────────────────────────────────────
    p = sub.add_parser("doctor", help="Preflight: token, config discovery, version pin")
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_doctor)

    # ── clients ───────────────────────────────────────────────────────────────
    p = sub.add_parser("clients", help="List registered clients (clients.yaml + env.d)")
    p.set_defaults(func=cmd_clients)

    # ── whoami ────────────────────────────────────────────────────────────────
    p = sub.add_parser("whoami", help="Verify GITHUB_TOKEN and print GitHub login")
    p.set_defaults(func=cmd_whoami)

    # ── onboard ───────────────────────────────────────────────────────────────
    add_onboard_parser(sub)

    # ── init-client ───────────────────────────────────────────────────────────
    p = sub.add_parser(
        "init-client",
        help="Day-1/Day-N: ensure teams, repo, gitflow, board on GitHub",
    )
    _add_scope_flags(p)
    _add_apply_flags(p)
    p.add_argument("--config-dir", default="", help="Path to config/ dir (default: ./config)")
    p.set_defaults(func=cmd_init_client)

    # ── apply-scaffold ────────────────────────────────────────────────────────
    p = sub.add_parser(
        "apply-scaffold",
        help="Run cookiecutter scaffold from scaffold-<org>.yaml",
    )
    _add_scope_flags(p)
    _add_apply_flags(p)
    p.add_argument("--force", action="store_true", help="Overwrite existing scaffold output")
    p.add_argument("--config-dir", default="", help="Path to config/ dir (default: ./config)")
    p.set_defaults(func=cmd_apply_scaffold)

    # ── apply-harness ─────────────────────────────────────────────────────────
    p = sub.add_parser(
        "apply-harness",
        help="Pin constitution submodule + seed agent skills from harness-<org>.yaml",
    )
    _add_scope_flags(p)
    _add_apply_flags(p)
    p.add_argument("--config-dir", default="", help="Path to config/ dir (default: ./config)")
    p.set_defaults(func=cmd_apply_harness)

    # ── check-harness ─────────────────────────────────────────────────────────
    p = sub.add_parser(
        "check-harness",
        help="Verify harness pins, submodule state, and AGENTS.md",
    )
    _add_scope_flags(p)
    p.add_argument("--config-dir", default="", help="Path to config/ dir (default: ./config)")
    p.set_defaults(func=cmd_check_harness)

    # ── status ────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "status",
        help="Programme readiness checklist + single best NEXT: command",
    )
    _add_scope_flags(p)
    p.add_argument("--config-dir", default="", help="Path to config/ dir (default: ./config)")
    p.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        apply_client_context(getattr(args, "client", "") or "")
    except ClientRegistryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        return args.func(args)
    except GitHubError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        body = getattr(exc, "body", "")
        if body:
            print(body, file=sys.stderr)
        return 1
    except (
        RuntimeError,
        ValueError,
        FileNotFoundError,
        SchemaError,
        ClientRegistryError,
        OnboardingError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
