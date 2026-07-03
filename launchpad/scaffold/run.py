"""Run cookiecutter scaffold for an app repo."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from launchpad.config import load_harness_config, resolve_workspace_parent, tenant_root
from launchpad.scaffold.errors import ScaffoldError
from launchpad.scaffold.profiles import ScaffoldProfile, get_profile, normalize_options


@dataclass
class ScaffoldPlan:
    profile: str
    repo: str
    template: str
    output_dir: Path
    target_dir: Path
    context: dict[str, str]
    with_harness: bool
    with_gitflow: bool
    dry_run: bool
    force: bool = False


def _resolve_workspace(
    cfg: dict[str, Any],
    workspace: Path | None,
    *,
    config_path: Path | None = None,
) -> Path:
    if workspace is not None:
        return workspace.resolve()
    if config_path is not None:
        config_dir = config_path.resolve().parent
        if config_dir.name == "config":
            return resolve_workspace_parent(harness_cfg=cfg)
        default = str(cfg.get("default_workspace", ".."))
        return (config_dir / default).resolve()
    return resolve_workspace_parent(harness_cfg=cfg)


def _repo_meta(cfg: dict[str, Any], repo_name: str) -> dict[str, Any]:
    repos = cfg.get("repos") or {}
    if repo_name not in repos:
        known = ", ".join(sorted(repos.keys()))
        raise ScaffoldError(f"repo {repo_name!r} not in harness config (known: {known})")
    meta = repos[repo_name]
    if not isinstance(meta, dict):
        raise ScaffoldError(f"invalid repo entry for {repo_name!r}")
    return meta


def _infer_profile(cfg: dict[str, Any], repo_name: str, explicit: str) -> str:
    if explicit:
        return get_profile(explicit).name
    meta = _repo_meta(cfg, repo_name)
    profile_name = str(meta.get("profile", "")).strip()
    if not profile_name:
        raise ScaffoldError(f"repo {repo_name!r} has no profile — pass --profile")
    return get_profile(profile_name).name


def _resolve_template(
    profile: ScaffoldProfile,
    *,
    workspace: Path,
    explicit: str,
) -> str:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_dir():
            return str(path.resolve())
        return explicit

    env_path = os.environ.get(profile.template_env, "").strip()
    if env_path:
        path = Path(env_path).expanduser()
        if path.is_dir():
            return str(path.resolve())
        return env_path

    candidates = [
        workspace / "python-fastapi-foundation",
        workspace.parent / "python-fastapi-foundation",
    ]
    try:
        candidates.append(tenant_root().parent / "python-fastapi-foundation")
    except FileNotFoundError:
        pass
    if profile.name == "python-backend":
        for candidate in candidates:
            if (candidate / "cookiecutter.json").is_file():
                return str(candidate.resolve())

    return profile.template_default


def build_context(
    profile: ScaffoldProfile,
    *,
    repo_name: str,
    repo_meta: dict[str, Any],
    cli_options: dict[str, str],
) -> dict[str, str]:
    ctx = dict(profile.defaults)
    ctx["service_name"] = repo_name
    ctx["service_description"] = str(repo_meta.get("service_name", repo_name.replace("-", " ").title()))

    scaffold_block = repo_meta.get("scaffold") or {}
    if scaffold_block and not isinstance(scaffold_block, dict):
        raise ScaffoldError(f"repo {repo_name!r} scaffold block must be a mapping")
    ctx.update({str(k): str(v) for k, v in scaffold_block.items()})
    ctx.update(cli_options)
    return normalize_options(profile, ctx)


def build_plan(
    *,
    config_path: str | Path,
    repo_name: str,
    profile_name: str = "",
    workspace: Path | None = None,
    template: str = "",
    options: dict[str, str] | None = None,
    with_harness: bool = False,
    with_gitflow: bool = False,
    dry_run: bool = True,
    force: bool = False,
) -> ScaffoldPlan:
    cfg = load_harness_config(config_path)
    resolved_profile_name = _infer_profile(cfg, repo_name, profile_name)
    profile = get_profile(resolved_profile_name)
    if not profile.implemented:
        raise ScaffoldError(
            f"scaffold profile {profile.name!r} is registered but not implemented yet "
            f"(planned: {profile.template_default})"
        )

    repo_meta = _repo_meta(cfg, repo_name)
    harness_path = Path(config_path).resolve()
    output_dir = _resolve_workspace(cfg, workspace, config_path=harness_path)
    template_ref = _resolve_template(profile, workspace=output_dir, explicit=template)
    context = build_context(
        profile,
        repo_name=repo_name,
        repo_meta=repo_meta,
        cli_options=options or {},
    )
    target_dir = output_dir / repo_name

    return ScaffoldPlan(
        profile=profile.name,
        repo=repo_name,
        template=template_ref,
        output_dir=output_dir,
        target_dir=target_dir,
        context=context,
        with_harness=with_harness,
        with_gitflow=with_gitflow,
        dry_run=dry_run,
        force=force,
    )


def format_plan(plan: ScaffoldPlan) -> str:
    lines = [
        f"scaffold profile={plan.profile} repo={plan.repo} dry_run={plan.dry_run} force={plan.force}",
        f"  template: {plan.template}",
        f"  output:   {plan.target_dir}",
        "  cookiecutter context:",
    ]
    for key in sorted(plan.context):
        lines.append(f"    {key}: {plan.context[key]}")
    if plan.with_harness:
        lines.append(f"  post: sync-harness --repo {plan.repo}")
    if plan.with_gitflow:
        lines.append(f"  post: setup-gitflow --repo {plan.repo}")
    if plan.force and plan.target_dir.exists():
        lines.append(f"  force: overlay foundation into existing {plan.target_dir} (preserves .git)")
    return "\n".join(lines)


def _overlay_tree(src: Path, dst: Path) -> None:
    """Copy generated scaffold files into an existing repo (overwrite matching paths only)."""
    if not src.is_dir():
        raise ScaffoldError(f"generated scaffold missing: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _run_cookiecutter(plan: ScaffoldPlan) -> None:
    try:
        from cookiecutter.main import cookiecutter as run_cookiecutter_cli
    except ImportError as exc:
        raise ScaffoldError(
            "cookiecutter is required for scaffold — reinstall launchpad or run: pip install cookiecutter"
        ) from exc

    print(f"[scaffold] template={plan.template}")
    overlay = plan.force and plan.target_dir.exists()

    if overlay:
        print(f"[scaffold] force: overlay into existing {plan.target_dir} (preserves .git)")
        temp_parent = Path(tempfile.mkdtemp(prefix="launchpad-scaffold-"))
        try:
            print(f"[scaffold] generating {plan.repo} in temp, then merging into target")
            run_cookiecutter_cli(
                plan.template,
                no_input=True,
                extra_context=plan.context,
                output_dir=str(temp_parent),
            )
            generated = temp_parent / plan.repo
            if not generated.is_dir():
                raise ScaffoldError(f"cookiecutter finished but {generated} was not created")
            _overlay_tree(generated, plan.target_dir)
        finally:
            shutil.rmtree(temp_parent, ignore_errors=True)
        return

    if plan.target_dir.exists():
        raise ScaffoldError(
            f"target already exists: {plan.target_dir} "
            f"(clone the repo first, then pass --apply --force to overlay foundation files)"
        )

    print(f"[scaffold] generating {plan.repo} → {plan.target_dir}")
    run_cookiecutter_cli(
        plan.template,
        no_input=True,
        extra_context=plan.context,
        output_dir=str(plan.output_dir),
    )

    if not plan.target_dir.is_dir():
        raise ScaffoldError(f"cookiecutter finished but {plan.target_dir} was not created")


def _run_post_steps(plan: ScaffoldPlan, *, config_path: str | Path) -> None:
    if plan.dry_run:
        return

    cfg = load_harness_config(config_path)
    org = str(cfg.get("org", ""))

    if plan.with_gitflow:
        from launchpad.config import discover_tenant_config
        from launchpad.gitflow import run as run_gitflow
        from launchpad.github_client import GitHubClient

        gitflow_path = discover_tenant_config("gitflow", org=org)
        print(f"[scaffold] post: setup-gitflow --repo {plan.repo}")
        with GitHubClient(dry_run=False) as client:
            run_gitflow(client, org=org, config_path=gitflow_path, filter_repo=plan.repo)

    if plan.with_harness:
        print(f"[scaffold] post: sync-harness --repo {plan.repo}")
        from launchpad import harness

        harness.run_sync(
            config_path=config_path,
            repo_name=plan.repo,
            workspace=plan.output_dir,
            dry_run=False,
        )


def run_scaffold(
    *,
    config_path: str | Path,
    repo_name: str,
    profile_name: str = "",
    workspace: Path | None = None,
    template: str = "",
    options: dict[str, str] | None = None,
    with_harness: bool = False,
    with_gitflow: bool = False,
    dry_run: bool = True,
    force: bool = False,
) -> ScaffoldPlan:
    plan = build_plan(
        config_path=config_path,
        repo_name=repo_name,
        profile_name=profile_name,
        workspace=workspace,
        template=template,
        options=options,
        with_harness=with_harness,
        with_gitflow=with_gitflow,
        dry_run=dry_run,
        force=force,
    )
    print(format_plan(plan))
    if dry_run:
        if plan.target_dir.exists() and plan.force:
            print(
                f"[scaffold] dry-run — would overlay foundation into existing {plan.target_dir} "
                f"with --apply --force (preserves .git)"
            )
        elif plan.target_dir.exists():
            print(
                f"[scaffold] dry-run — target exists: {plan.target_dir} "
                f"(use --apply --force to overlay foundation files)"
            )
        else:
            print("[scaffold] dry-run — pass --apply to generate")
        return plan

    _run_cookiecutter(plan)
    _run_post_steps(plan, config_path=config_path)
    print(f"[scaffold] done: {plan.target_dir}")
    return plan
