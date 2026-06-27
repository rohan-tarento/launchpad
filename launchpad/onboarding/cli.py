"""CLI handlers for launchpad onboard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from launchpad.onboarding.errors import OnboardingError
from launchpad.onboarding.plan import build_plan, format_plan
from launchpad.onboarding.spec import load_onboarding_spec


def _spec_path(args: argparse.Namespace) -> Path:
    raw = getattr(args, "spec", "") or ""
    if not raw:
        raise OnboardingError("--spec is required (path to onboarding.yaml)")
    return Path(raw).expanduser().resolve()


def cmd_onboard_plan(args: argparse.Namespace) -> int:
    spec_path = _spec_path(args)
    spec = load_onboarding_spec(spec_path)
    plan = build_plan(spec, spec_path=spec_path)
    print(format_plan(plan))
    return 0


def cmd_onboard_show(args: argparse.Namespace) -> int:
    spec_path = _spec_path(args)
    spec = load_onboarding_spec(spec_path)
    out = {k: v for k, v in spec.items() if not str(k).startswith("_")}
    print(yaml.safe_dump(out, sort_keys=False, default_flow_style=False))
    return 0


def cmd_onboard_apply(args: argparse.Namespace) -> int:
    print(
        "onboard apply is not implemented yet (PR3).\n"
        "Use: launchpad onboard plan --spec <path> to preview.",
        file=sys.stderr,
    )
    return 1


def cmd_onboard_interview(args: argparse.Namespace) -> int:
    print(
        "Interactive onboard interview is not implemented yet (PR2).\n"
        "Copy examples/onboarding-kola.yaml and edit, or:\n"
        "  launchpad onboard show --spec examples/onboarding-kola.yaml",
        file=sys.stderr,
    )
    return 1


def add_onboard_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "onboard",
        help="Tenant onboarding — interview, plan, apply from onboarding.yaml",
    )
    onboard_sub = p.add_subparsers(dest="onboard_command", required=True)

    p_interview = onboard_sub.add_parser(
        "interview",
        help="Interactive Q&A → write onboarding.yaml (PR2)",
    )
    p_interview.add_argument(
        "--output",
        default="",
        help="Spec output path (default: <workspace>/onboarding.yaml)",
    )
    p_interview.set_defaults(func=cmd_onboard_interview)

    for name, help_text, handler in (
        ("plan", "Dry-run preview from onboarding.yaml", cmd_onboard_plan),
        ("show", "Print normalized onboarding.yaml", cmd_onboard_show),
        ("apply", "Scaffold tenant from onboarding.yaml (PR3)", cmd_onboard_apply),
    ):
        sub_p = onboard_sub.add_parser(name, help=help_text)
        sub_p.add_argument(
            "--spec",
            required=True,
            help="Path to onboarding.yaml (e.g. ~/Workspace/handson/kola/onboarding.yaml)",
        )
        sub_p.set_defaults(func=handler)
