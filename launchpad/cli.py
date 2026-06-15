"""CLI entry point for launchpad factory automation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from launchpad import bootstrap_org, bootstrap_teams, gitflow, harness, platform, project, seed_work
from launchpad.config import discover_tenant_config, load_org_config, load_project_config
from launchpad.doctor import run as run_doctor
from launchpad.adapters.gitlab.client import GitLabError
from launchpad.github_client import GitHubClient, GitHubError
from launchpad.verify.runner import VerifyError, run as run_verify

load_env = __import__("launchpad.config", fromlist=["load_env"]).load_env
load_env()


def _config_path(args: argparse.Namespace, kind: str) -> str:
    if args.config:
        return args.config
    return str(discover_tenant_config(kind, org=getattr(args, "org", "") or ""))


def _add_apply_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True, help="print actions only (default)")
    group.add_argument("--apply", action="store_true", help="execute against GitHub API")


def _dry_run_from_args(args: argparse.Namespace) -> bool:
    return not getattr(args, "apply", False)


def _client(args: argparse.Namespace) -> GitHubClient:
    return GitHubClient(dry_run=_dry_run_from_args(args))


def _org_from_config(config_path: str) -> str:
    p = Path(config_path)
    if p.name.startswith("org-"):
        return load_org_config(p)["org"]
    if p.name.startswith("project-"):
        return load_project_config(p)["org"]
    return ""


def cmd_bootstrap_org(args: argparse.Namespace) -> int:
    config = _config_path(args, "org")
    with _client(args) as client:
        bootstrap_org.run(client, org=args.org or "", config_path=config)
    return 0


def cmd_bootstrap_teams(args: argparse.Namespace) -> int:
    config = _config_path(args, "org")
    with _client(args) as client:
        bootstrap_teams.run(client, org=args.org or "", config_path=config)
    return 0


def cmd_setup_gitflow(args: argparse.Namespace) -> int:
    config = _config_path(args, "gitflow")
    with _client(args) as client:
        gitflow.run(
            client,
            org=args.org or "",
            config_path=config,
            filter_repo=args.repo or "",
            workspace=args.workspace,
            with_templates=args.with_templates if args.with_templates else None,
            init_empty=args.init_empty if args.init_empty else None,
            require_ci=args.require_ci if args.require_ci else None,
            branch_naming=args.branch_naming if args.branch_naming else None,
        )
    return 0


def cmd_bootstrap_project(args: argparse.Namespace) -> int:
    config = _config_path(args, "project")
    with _client(args) as client:
        project.run(client, org=args.org or "", config_path=config)
    return 0


def cmd_seed_work(args: argparse.Namespace) -> int:
    if not args.config:
        print(
            "seed-work requires --config work/<initiative>.yaml "
            "(generate via /generate-work-manifest)",
            file=sys.stderr,
        )
        return 1

    from launchpad.config import tenant_root
    from launchpad.forge import resolve_forge_for_manifest

    manifest_path = args.config
    if not Path(manifest_path).is_absolute():
        manifest_path = str(tenant_root() / manifest_path)

    forge_type, gitlab_host = resolve_forge_for_manifest(manifest_path)
    if forge_type == "gitlab":
        from launchpad.adapters.gitlab.client import GitLabClient
        from launchpad.adapters.gitlab import seed_work as gitlab_seed_work

        project_cfg: str | None = None
        try:
            project_cfg = str(discover_tenant_config("project", org=args.org or ""))
        except (FileNotFoundError, ValueError):
            pass
        with GitLabClient(dry_run=_dry_run_from_args(args), host=gitlab_host) as client:
            gitlab_seed_work.run(
                client,
                manifest_path=manifest_path,
                project_config_path=project_cfg,
            )
        return 0

    with _client(args) as client:
        seed_work.run(client, manifest_path=manifest_path, org=args.org or "")
    return 0


def cmd_setup_platform(args: argparse.Namespace) -> int:
    config = _config_path(args, "platform")
    with _client(args) as client:
        platform.run(client, config_path=config, org=args.org or "")
    return 0


def cmd_verify_platform(args: argparse.Namespace) -> int:
    config = _config_path(args, "verify-platform")
    org = args.org or _org_from_config(config)
    phase = args.phase or None
    try:
        with GitHubClient(dry_run=False) as client:
            run_verify(client, config_path=config, org=org, phase=phase)
    except VerifyError:
        return 1
    return 0


def cmd_whoami(args: argparse.Namespace) -> int:
    with GitHubClient(dry_run=False) as client:
        print(client.whoami())
    return 0


def cmd_sync_harness(args: argparse.Namespace) -> int:
    config = _config_path(args, "harness")
    harness.run_sync(
        config_path=config,
        repo_name=args.repo,
        workspace=args.workspace,
        dry_run=_dry_run_from_args(args),
        skip_agents=args.skip_agents,
    )
    return 0


def cmd_verify_harness(args: argparse.Namespace) -> int:
    config = _config_path(args, "harness")
    harness.run_verify(
        config_path=config,
        repo_name=args.repo or "",
        workspace=args.workspace,
    )
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    return run_doctor(verbose=args.verbose)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="launchpad",
        description="Launchpad forge factory automation (GitHub v1; GitLab roadmap). "
        "Run from a tenant <client>-meta workspace. Developers still use `gh` for day-to-day PRs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="Preflight: tenant root, token, config discovery")
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("bootstrap-org", help="Create repos + labels (OrgConfig YAML)")
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_bootstrap_org)

    p = sub.add_parser("bootstrap-teams", help="Create engineering teams (OrgConfig YAML)")
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_bootstrap_teams)

    p = sub.add_parser("setup-gitflow", help="develop branch + protection + optional rulesets")
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    p.add_argument("--repo", default="")
    p.add_argument("--workspace", type=Path, default=None)
    p.add_argument("--with-templates", action="store_true")
    p.add_argument("--init-empty", action="store_true")
    p.add_argument("--require-ci", action="store_true")
    p.add_argument("--branch-naming", action="store_true")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_setup_gitflow)

    p = sub.add_parser("bootstrap-project", help="Org project board + fields + repo links")
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_bootstrap_project)

    p = sub.add_parser(
        "seed-work",
        help="Create issues + Project items from a WorkManifest YAML",
    )
    p.add_argument("--config", default="")
    p.add_argument("--org", default="")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_seed_work)

    p = sub.add_parser("seed-issues", help="Alias for seed-work")
    p.add_argument("--config", default="")
    p.add_argument("--org", default="")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_seed_work)

    p = sub.add_parser(
        "setup-platform",
        help="Platform baseline from PlatformManifest (org + teams + gitflow + board + verify)",
    )
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_setup_platform)

    p = sub.add_parser(
        "verify-platform",
        help="Platform verify from VerifyManifest (ready for backlog?)",
    )
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    p.add_argument(
        "--phase",
        choices=["scopes", "applied"],
        default="",
        help="Run only scopes or applied checks (default: all)",
    )
    p.set_defaults(func=cmd_verify_platform)

    p = sub.add_parser(
        "verify-factory",
        help="Alias for verify-platform",
    )
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    p.add_argument("--phase", choices=["scopes", "applied"], default="")
    p.set_defaults(func=cmd_verify_platform)

    p = sub.add_parser("whoami", help="Verify GITHUB_TOKEN and print login")
    p.set_defaults(func=cmd_whoami)

    p = sub.add_parser(
        "sync-harness",
        help="Pin rules submodule, seed prayog-skills bundle, .harness-pin.yaml, AGENTS.md",
    )
    p.add_argument("--repo", required=True, help="App repo name (e.g. example-api)")
    p.add_argument("--config", default="")
    p.add_argument("--workspace", type=Path, default=None, help="Parent of app clones (default: meta parent)")
    p.add_argument("--skip-agents", action="store_true", help="Do not overwrite AGENTS.md")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_sync_harness)

    p = sub.add_parser(
        "verify-harness",
        help="Check harness pins and submodules in local app clones",
    )
    p.add_argument("--repo", default="", help="Single repo (default: all in HarnessConfig)")
    p.add_argument("--config", default="")
    p.add_argument("--workspace", type=Path, default=None)
    p.set_defaults(func=cmd_verify_harness)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (GitHubError, GitLabError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        body = getattr(exc, "body", "")
        if body:
            print(body, file=sys.stderr)
        return 1
    except (RuntimeError, ValueError, FileNotFoundError, VerifyError, harness.HarnessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
