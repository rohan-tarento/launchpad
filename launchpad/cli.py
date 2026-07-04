"""CLI entry point for launchpad factory automation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from launchpad import __version__
from launchpad import bootstrap_org, bootstrap_teams, gitflow, harness, platform, project, repo_seed, seed_work, wiki
from launchpad.clients import ClientRegistryError, apply_client_context, format_clients_table
from launchpad.config import discover_tenant_config, load_org_config, load_project_config
from launchpad.doctor import run as run_doctor
from launchpad.adapters.gitlab.client import GitLabError
from launchpad.github_client import GitHubClient, GitHubError
from launchpad.verify.runner import VerifyError, run as run_verify
from launchpad.wiki import WikiError
from launchpad.onboarding.cli import add_onboard_parser
from launchpad.onboarding.errors import OnboardingError
from launchpad.scaffold.cli import (
    add_scaffold_app_parser,
    add_scaffold_meta_parser,
    parse_scaffold_options,
)
from launchpad.scaffold.errors import ScaffoldError
from launchpad.scaffold.run import run_scaffold

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
        )
    return 0


def cmd_seed_repos(args: argparse.Namespace) -> int:
    config = _config_path(args, "gitflow")
    with _client(args) as client:
        repo_seed.run(
            client,
            org=args.org or "",
            config_path=config,
            filter_repo=args.repo or "",
        )
    return 0


def cmd_clone_repos(args: argparse.Namespace) -> int:
    from launchpad import workspace_clone

    config = _config_path(args, "gitflow")
    with _client(args) as client:
        workspace_clone.run(
            client,
            org=args.org or "",
            config_path=config,
            filter_repo=args.repo or "",
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
            "(from /spec-implementation-plan §9, or hand-authored work/INIT-*.yaml)",
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


def cmd_sync_catalog(args: argparse.Namespace) -> int:
    from launchpad.service_catalog import run_sync

    config = _config_path(args, "service-catalog") if not args.config else args.config
    run_sync(
        org=args.org or "",
        config_path=config,
        gitflow_path=args.gitflow or None,
        dry_run=_dry_run_from_args(args),
    )
    return 0


def cmd_sync_harness_app(args: argparse.Namespace) -> int:
    config = _config_path(args, "harness")
    harness.run_sync_app(
        config_path=config,
        repo_name=args.repo,
        workspace=args.workspace,
        dry_run=_dry_run_from_args(args),
        skip_agents=args.skip_agents,
    )
    return 0


def cmd_sync_harness_meta(args: argparse.Namespace) -> int:
    config = _config_path(args, "harness")
    harness.run_sync_meta(
        config_path=config,
        dry_run=_dry_run_from_args(args),
        skip_agents=args.skip_agents,
    )
    return 0


def cmd_verify_harness_app(args: argparse.Namespace) -> int:
    config = _config_path(args, "harness")
    harness.run_verify_app(
        config_path=config,
        repo_name=args.repo or "",
        workspace=args.workspace,
    )
    return 0


def cmd_verify_harness_meta(args: argparse.Namespace) -> int:
    config = _config_path(args, "harness")
    harness.run_verify_meta(config_path=config)
    return 0


def cmd_publish_wiki(args: argparse.Namespace) -> int:
    config = _config_path(args, "wiki")
    wiki.run(
        config_path=config,
        org=args.org or "",
        dry_run=_dry_run_from_args(args),
    )
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    return run_doctor(verbose=args.verbose)


def cmd_clients(args: argparse.Namespace) -> int:
    print(format_clients_table())
    return 0


def cmd_scaffold_app(args: argparse.Namespace) -> int:
    config = _config_path(args, "harness")
    run_scaffold(
        config_path=config,
        repo_name=args.repo,
        profile_name=args.profile or "",
        workspace=args.workspace,
        template=args.template or "",
        options=parse_scaffold_options(args),
        dry_run=_dry_run_from_args(args),
        force=args.force,
    )
    return 0


def cmd_scaffold_meta(args: argparse.Namespace) -> int:
    from launchpad.scaffold.meta_run import run_scaffold_meta

    run_scaffold_meta(
        meta_repo=args.meta_repo or "",
        target_dir=args.target,
        template=args.template or "",
        options=parse_scaffold_options(args),
        dry_run=_dry_run_from_args(args),
        force=args.force,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="launchpad",
        description="Launchpad forge factory automation (GitHub v1; GitLab roadmap). "
        "Run from a tenant <client>-meta workspace, or use --client from "
        "~/.config/launchpad/clients.yaml. Developers still use `gh` for day-to-day PRs.",
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
        help="print launchpad version and exit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("clients", help="List configured clients (clients.yaml + env.d)")
    p.set_defaults(func=cmd_clients)

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

    p = sub.add_parser("setup-gitflow", help="develop branch + protection (policy from gitflow YAML)")
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    p.add_argument("--repo", default="", help="limit to one repo (debug re-run only)")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_setup_gitflow)

    p = sub.add_parser(
        "seed-repos",
        help="Seed main + develop + default branch develop for all gitflow repos",
    )
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    p.add_argument("--repo", default="", help="limit to one repo (debug re-run only)")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_seed_repos)

    p = sub.add_parser(
        "clone-repos",
        help="Clone gitflow repos locally on develop (workspace parent from gitflow options)",
    )
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    p.add_argument("--repo", default="", help="limit to one repo (debug re-run only)")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_clone_repos)

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
        "sync-catalog",
        help="Merge config/service-catalog-<org>.yaml from gitflow (preserves curated owns/depends_on)",
    )
    p.add_argument("--org", default="")
    p.add_argument("--config", default="", help="Catalog path (default: config/service-catalog-<org>.yaml)")
    p.add_argument("--gitflow", default="", help="Gitflow config (default: config/gitflow-<org>.yaml)")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_sync_catalog)

    p = sub.add_parser(
        "sync-harness-app",
        help="Pin rules submodule, seed prayog dev bundle, .harness-pin.yaml, AGENTS.md (app repos)",
    )
    p.add_argument("--repo", required=True, help="App repo name (e.g. example-api)")
    p.add_argument("--config", default="")
    p.add_argument("--workspace", type=Path, default=None, help="Parent of app clones (default: meta parent)")
    p.add_argument("--skip-agents", action="store_true", help="Do not overwrite AGENTS.md")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_sync_harness_app)

    p = sub.add_parser(
        "sync-harness-meta",
        help="Seed PM prayog bundle + community prd skill, .harness-pin.yaml, AGENTS.md (tenant meta)",
    )
    p.add_argument("--config", default="")
    p.add_argument("--skip-agents", action="store_true", help="Do not overwrite AGENTS.md")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_sync_harness_meta)

    p = sub.add_parser(
        "verify-harness-app",
        help="Check harness pins and submodules in local app clones",
    )
    p.add_argument("--repo", default="", help="Single repo (default: all in HarnessConfig)")
    p.add_argument("--config", default="")
    p.add_argument("--workspace", type=Path, default=None)
    p.set_defaults(func=cmd_verify_harness_app)

    p = sub.add_parser(
        "verify-harness-meta",
        help="Check harness pins and PM skills in tenant meta",
    )
    p.add_argument("--config", default="")
    p.set_defaults(func=cmd_verify_harness_meta)

    p = sub.add_parser(
        "publish-wiki",
        help="Publish wiki/*.md to GitHub Wiki (WikiConfig YAML)",
    )
    p.add_argument("--org", default="")
    p.add_argument("--config", default="")
    _add_apply_flags(p)
    p.set_defaults(func=cmd_publish_wiki)

    add_scaffold_app_parser(sub).set_defaults(func=cmd_scaffold_app)
    add_scaffold_meta_parser(sub).set_defaults(func=cmd_scaffold_meta)

    add_onboard_parser(sub)

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
    except (GitHubError, GitLabError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        body = getattr(exc, "body", "")
        if body:
            print(body, file=sys.stderr)
        return 1
    except (
        RuntimeError,
        ValueError,
        FileNotFoundError,
        VerifyError,
        harness.HarnessError,
        WikiError,
        ClientRegistryError,
        OnboardingError,
        ScaffoldError,
        gitflow.GitflowError,
        repo_seed.RepoSeedError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
