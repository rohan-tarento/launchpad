"""Apply OnboardingSpec — scaffold tenant meta + registry."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import launchpad
from launchpad.clients import apply_client_context, ENV_D_DIR
from launchpad.doctor import run as run_doctor
from launchpad.github_client import GitHubClient
from launchpad.onboarding.context import OnboardingContext
from launchpad.onboarding.errors import OnboardingError
from launchpad.onboarding.plan import build_plan, format_plan
from launchpad.onboarding.registry import patch_clients_registry, write_secrets_stub
from launchpad.onboarding.render import all_config_renders, render_playbook_readme
from launchpad.onboarding.templates_gen import all_template_renders
from launchpad.paths import kit_root
from launchpad import platform


def _copy_skeleton(meta_path: Path) -> None:
    skeleton = kit_root() / "examples" / "tenant-meta"
    if not skeleton.is_dir():
        raise OnboardingError(f"kit skeleton not found: {skeleton}")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    if meta_path.is_dir():
        return
    shutil.copytree(skeleton, meta_path)


def _write_files(meta_path: Path, files: dict[str, str]) -> list[str]:
    written: list[str] = []
    for rel, content in files.items():
        dest = meta_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        written.append(str(dest))
    return written


def _remove_example_configs(meta_path: Path, org: str) -> None:
    config_dir = meta_path / "config"
    if not config_dir.is_dir():
        return
    for path in config_dir.glob("*-example*.yaml"):
        path.unlink(missing_ok=True)
    for path in config_dir.glob("org-*.yaml"):
        if path.name != f"org-{org}.yaml":
            path.unlink(missing_ok=True)


def run_apply(
    spec: dict,
    *,
    spec_path: Path,
    skip_registry: bool = False,
    skip_doctor: bool = False,
    run_platform: bool = False,
) -> None:
    ctx = OnboardingContext(spec)
    meta_path = Path(spec["_meta_path"])
    org = ctx.org
    client_id = ctx.client_id

    print("=== onboard apply ===")
    plan = build_plan(spec, spec_path=spec_path)
    print(f"Spec:   {spec_path}")
    print(f"Client: {plan.client_id} | Org: {plan.org} | Forge: {plan.forge_type}")
    print(f"Meta:   {meta_path}")
    for w in plan.warnings:
        print(f"WARN: {w}")
    print("")

    _copy_skeleton(meta_path)
    _remove_example_configs(meta_path, org)

    files: dict[str, str] = {}
    files.update(all_config_renders(ctx))
    if ctx.spec["overrides"]["generate_playbook_hub"]:
        files["playbook/README.md"] = render_playbook_readme(ctx)
    files.update(all_template_renders(ctx))

    written = _write_files(meta_path, files)
    version_path = meta_path / ".launchpad-version"
    version_path.write_text(f"{launchpad.__version__}\n", encoding="utf-8")
    written.append(str(version_path))

    print(f"Scaffolded: {meta_path}")
    print(f"Wrote {len(written)} generated file(s)")

    if not skip_registry and spec["registry"]["register_client"]:
        patch_clients_registry(
            client_id=client_id,
            meta_path=meta_path,
            forge_type=ctx.forge_type,
            set_default=spec["registry"]["set_default"],
        )
        print(f"Patched: ~/.config/launchpad/clients.yaml (+ client {client_id})")
        if spec["registry"]["secrets_stub"]:
            env_path = write_secrets_stub(client_id=client_id, forge_type=ctx.forge_type)
            print(f"Secrets stub: {env_path}")

    if run_platform or spec["provision"]["run_setup_platform"]:
        if ctx.forge_type != "github":
            print("WARN: setup-platform apply skipped — GitHub-only for automated platform bootstrap")
        else:
            platform_cfg = meta_path / f"config/platform-{org}.yaml"
            with GitHubClient(dry_run=False) as client:
                platform.run(client, config_path=str(platform_cfg), org=org)
            print("Ran: setup-platform --apply")

    if not skip_doctor and spec["provision"]["run_doctor"]:
        os.environ["LAUNCHPAD_TENANT_ROOT"] = str(meta_path)
        os.environ["LAUNCHPAD_CLIENT"] = client_id
        apply_client_context(client_id)
        code = run_doctor(verbose=False)
        if code != 0:
            raise OnboardingError("doctor failed after apply — fix warnings and re-run doctor")

    print("")
    print("=== onboard apply complete ===")
    print(f"Spec:  {spec_path}")
    print(f"Meta:  {meta_path}")
    print("")
    print("Manual next steps:")
    print(f"  1. Edit {ENV_D_DIR / (client_id + '.env')} — paste forge token")
    print(f"  2. Create remote {org}/{ctx.meta_repo} and push meta")
    print(f"  3. launchpad --client {client_id} setup-platform --config config/platform-{org}.yaml --dry-run")
