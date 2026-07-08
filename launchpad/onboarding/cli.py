"""CLI handlers for launchpad onboard.

Public surface: onboard interview (only)

Legacy subcommands (apply, plan, show) are kept as internal library code
but removed from the public help.  They will be fully deleted in v0.6.0.
"""

from __future__ import annotations

import argparse

from launchpad.onboarding.errors import OnboardingError
from launchpad.onboarding.interview import run_interview


def cmd_onboard_interview(args: argparse.Namespace) -> int:
    try:
        run_interview()
    except (KeyboardInterrupt, EOFError):
        print("\n\nInterrupted — no files written.")
        return 1
    except OnboardingError as exc:
        print(f"\nERROR: {exc}")
        return 1
    return 0


def add_onboard_parser(sub: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    p = sub.add_parser(
        "onboard",
        help="Onboard a new programme — interactive 4-question setup",
    )
    onboard_sub = p.add_subparsers(dest="onboard_command", required=True)

    p_interview = onboard_sub.add_parser(
        "interview",
        help="4 questions → writes config YAMLs, registry entry, and env stub",
    )
    p_interview.set_defaults(func=cmd_onboard_interview)
