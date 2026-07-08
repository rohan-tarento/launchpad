"""CLI handlers for launchpad onboard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from launchpad.onboarding.apply import run_apply
from launchpad.onboarding.errors import OnboardingError
from launchpad.onboarding.interview import run_interview
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
    spec_path = _spec_path(args)
    spec = load_onboarding_spec(spec_path)
    run_apply(
        spec,
        spec_path=spec_path,
        skip_registry=args.skip_registry,
        skip_doctor=args.skip_doctor,
        run_platform=args.with_platform,
    )
    return 0


def cmd_onboard_interview(args: argparse.Namespace) -> int:
    output = Path(args.output).expanduser().resolve() if args.output else None
    path = run_interview(output=output)
    print(f"Wrote onboarding spec → {path}")
    print(f"Next: launchpad onboard plan --spec {path}")
    return 0


def add_onboard_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "onboard",
        help="Tenant onboarding — interview, plan, apply from onboarding.yaml",
    )
    onboard_sub = p.add_subparsers(dest="onboard_command", required=True)

    p_interview = onboard_sub.add_parser(
        "interview",
        help="Interactive Q&A → write onboarding.yaml",
    )
    p_interview.add_argument(
        "--output",
        default="",
        help="Spec output path (default: ./onboarding.yaml in current directory)",
    )
    p_interview.set_defaults(func=cmd_onboard_interview)

    p_plan = onboard_sub.add_parser("plan", help="Dry-run preview from onboarding.yaml")
    p_plan.add_argument("--spec", required=True, help="Path to onboarding.yaml")
    p_plan.set_defaults(func=cmd_onboard_plan)

    p_show = onboard_sub.add_parser("show", help="Print normalized onboarding.yaml")
    p_show.add_argument("--spec", required=True, help="Path to onboarding.yaml")
    p_show.set_defaults(func=cmd_onboard_show)

    p_apply = onboard_sub.add_parser("apply", help="Scaffold tenant from onboarding.yaml")
    p_apply.add_argument("--spec", required=True, help="Path to onboarding.yaml")
    p_apply.add_argument(
        "--skip-registry",
        action="store_true",
        help="Do not patch ~/.config/launchpad/clients.yaml or env.d",
    )
    p_apply.add_argument(
        "--skip-doctor",
        action="store_true",
        help="Skip launchpad doctor after scaffold",
    )
    p_apply.add_argument(
        "--with-platform",
        action="store_true",
        help="Run setup-platform --apply after scaffold (GitHub + PAT required)",
    )
    p_apply.set_defaults(func=cmd_onboard_apply)
