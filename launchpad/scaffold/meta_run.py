"""Run cookiecutter scaffold for tenant meta repo."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from launchpad.scaffold.errors import ScaffoldError
from launchpad.scaffold.profiles import ScaffoldProfile, get_profile, normalize_options

# Paths never overwritten on scaffold-meta --force (product + harness + forge).
_META_PRESERVE_PREFIXES: tuple[str, ...] = (
    "prd/",
    "work/",
    "planning/",
    "programs/",
    "config/",
    ".github/",
    ".git/",
    ".harness-pin.yaml",
    "skills-lock.json",
    "AGENTS.md",
    ".agents/",
)


def _preserve_meta_path(rel: str) -> bool:
    normalized = rel.replace("\\", "/")
    for prefix in _META_PRESERVE_PREFIXES:
        if prefix.endswith("/"):
            if normalized == prefix.rstrip("/") or normalized.startswith(prefix):
                return True
        elif normalized == prefix:
            return True
    return False


def _overlay_meta_tree(src: Path, dst: Path) -> None:
    """Merge generated meta scaffold into existing tree; skip preserved paths."""
    if not src.is_dir():
        raise ScaffoldError(f"generated meta scaffold missing: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.rglob("*")):
        if item.is_dir():
            continue
        rel = item.relative_to(src).as_posix()
        target = dst / rel
        if _preserve_meta_path(rel) and target.exists():
            print(f"[scaffold-meta] preserve {rel}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        print(f"[scaffold-meta] overlay {rel}")


def _resolve_template(profile: ScaffoldProfile, *, explicit: str) -> str:
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
        Path.cwd().parent / "tenant-meta-foundation",
        Path.cwd() / "tenant-meta-foundation",
    ]
    try:
        from launchpad.config import tenant_root

        root = tenant_root()
        candidates.append(root.parent / "tenant-meta-foundation")
        # lab layout: ~/Workspace/handson/drivestream-lab/tenant-meta-foundation
        if len(root.parents) > 2:
            candidates.append(root.parents[2] / "drivestream-lab" / "tenant-meta-foundation")
    except FileNotFoundError:
        pass
    for candidate in candidates:
        if (candidate / "cookiecutter.json").is_file():
            return str(candidate.resolve())

    return profile.template_default


@dataclass
class MetaScaffoldPlan:
    profile: str
    meta_repo: str
    template: str
    target_dir: Path
    context: dict[str, str]
    dry_run: bool
    force: bool = False


def build_meta_context(
    profile: ScaffoldProfile,
    *,
    meta_repo: str,
    cli_options: dict[str, str],
) -> dict[str, str]:
    ctx = dict(profile.defaults)
    ctx["meta_repo"] = meta_repo
    ctx.update(cli_options)
    return normalize_options(profile, ctx)


def build_meta_plan(
    *,
    meta_repo: str = "",
    target_dir: Path | None = None,
    template: str = "",
    options: dict[str, str] | None = None,
    dry_run: bool = True,
    force: bool = False,
) -> MetaScaffoldPlan:
    profile = get_profile("tenant-meta")
    if not profile.implemented:
        raise ScaffoldError(f"scaffold profile {profile.name!r} is not implemented")

    resolved_meta = meta_repo.strip()
    if not resolved_meta:
        from launchpad.config import tenant_root

        resolved_meta = tenant_root().name

    if target_dir is None:
        from launchpad.config import tenant_root

        target_dir = tenant_root()
    else:
        target_dir = target_dir.resolve()

    template_ref = _resolve_template(profile, explicit=template)
    context = build_meta_context(profile, meta_repo=resolved_meta, cli_options=options or {})

    return MetaScaffoldPlan(
        profile=profile.name,
        meta_repo=resolved_meta,
        template=template_ref,
        target_dir=target_dir,
        context=context,
        dry_run=dry_run,
        force=force,
    )


def format_meta_plan(plan: MetaScaffoldPlan) -> str:
    lines = [
        f"scaffold-meta profile={plan.profile} repo={plan.meta_repo} dry_run={plan.dry_run} force={plan.force}",
        f"  template: {plan.template}",
        f"  output:   {plan.target_dir}",
        "  cookiecutter context:",
    ]
    for key in sorted(plan.context):
        lines.append(f"    {key}: {plan.context[key]}")
    if plan.force and plan.target_dir.exists():
        lines.append("  force: merge foundation (preserves prd/, work/, config/, harness artifacts)")
    return "\n".join(lines)


def _run_cookiecutter_meta(plan: MetaScaffoldPlan) -> None:
    try:
        from cookiecutter.main import cookiecutter as run_cookiecutter_cli
    except ImportError as exc:
        raise ScaffoldError(
            "cookiecutter is required for scaffold-meta — reinstall launchpad or run: pip install cookiecutter"
        ) from exc

    print(f"[scaffold-meta] template={plan.template}")
    overlay = plan.force and plan.target_dir.exists()

    if overlay:
        print(f"[scaffold-meta] force: merge into {plan.target_dir}")
        temp_parent = Path(tempfile.mkdtemp(prefix="launchpad-scaffold-meta-"))
        try:
            run_cookiecutter_cli(
                plan.template,
                no_input=True,
                extra_context=plan.context,
                output_dir=str(temp_parent),
            )
            generated = temp_parent / plan.meta_repo
            if not generated.is_dir():
                raise ScaffoldError(f"cookiecutter finished but {generated} was not created")
            _overlay_meta_tree(generated, plan.target_dir)
        finally:
            shutil.rmtree(temp_parent, ignore_errors=True)
        return

    if plan.target_dir.exists() and any(plan.target_dir.iterdir()):
        raise ScaffoldError(
            f"target already exists: {plan.target_dir} "
            f"(use --apply --force to merge kit upgrades)"
        )

    plan.target_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"[scaffold-meta] generating {plan.meta_repo} → {plan.target_dir.parent}")
    run_cookiecutter_cli(
        plan.template,
        no_input=True,
        extra_context=plan.context,
        output_dir=str(plan.target_dir.parent),
    )

    generated = plan.target_dir.parent / plan.meta_repo
    if not generated.is_dir():
        raise ScaffoldError(f"cookiecutter finished but {generated} was not created")
    if generated.resolve() != plan.target_dir.resolve():
        if plan.target_dir.exists():
            shutil.rmtree(plan.target_dir)
        generated.rename(plan.target_dir)


def run_scaffold_meta(
    *,
    meta_repo: str = "",
    target_dir: Path | None = None,
    template: str = "",
    options: dict[str, str] | None = None,
    dry_run: bool = True,
    force: bool = False,
) -> MetaScaffoldPlan:
    plan = build_meta_plan(
        meta_repo=meta_repo,
        target_dir=target_dir,
        template=template,
        options=options,
        dry_run=dry_run,
        force=force,
    )
    print(format_meta_plan(plan))
    if dry_run:
        if plan.target_dir.exists() and plan.force:
            print(f"[scaffold-meta] dry-run — would merge into {plan.target_dir} with --apply --force")
        elif plan.target_dir.exists():
            print("[scaffold-meta] dry-run — target exists (use --apply --force to merge)")
        else:
            print("[scaffold-meta] dry-run — pass --apply to generate")
        return plan

    _run_cookiecutter_meta(plan)
    print(f"[scaffold-meta] done: {plan.target_dir}")
    return plan
