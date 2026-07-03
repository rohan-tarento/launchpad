"""Build onboarding plan (dry-run preview) from OnboardingSpec."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from launchpad.clients import CLIENTS_FILE, ENV_D_DIR
from launchpad.paths import kit_root


@dataclass
class OnboardingPlan:
    spec_path: Path
    client_id: str
    org: str
    meta_repo: str
    meta_path: Path
    forge_type: str
    create_dirs: list[str] = field(default_factory=list)
    create_files: list[str] = field(default_factory=list)
    patch_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manual_steps: list[str] = field(default_factory=list)
    next_commands: list[str] = field(default_factory=list)


def _config_files(org: str) -> list[str]:
    base = f"config"
    return [
        f"{base}/org-{org}.yaml",
        f"{base}/platform-{org}.yaml",
        f"{base}/gitflow-{org}.yaml",
        f"{base}/harness-{org}.yaml",
        f"{base}/project-{org}.yaml",
        f"{base}/wiki-{org}.yaml",
        f"{base}/verify-platform-{org}.yaml",
    ]


def _template_files(spec: dict) -> list[str]:
    if not spec["overrides"]["generate_templates"]:
        return ["templates/README.md"]
    files = [
        "templates/README.md",
        "templates/AGENTS.md",
        "templates/CODEOWNERS.backend",
        "templates/CODEOWNERS.platform",
        "templates/harness-pin.yaml",
        "templates/pull_request_template.md",
    ]
    repos = spec["repos"]
    if any(r["profile"] == "frontend" for r in repos):
        files.extend(
            [
                "templates/CODEOWNERS.frontend",
                "templates/harness-pin.frontend.yaml",
            ]
        )
    if any(r["profile"] == "data_platform" for r in repos):
        files.extend(
            [
                
                "templates/CODEOWNERS.data-platform",
                "templates/harness-pin.data-platform.yaml",
            ]
        )
    if any(r["profile"] == "backend" for r in repos):
        pass  # python AGENTS already included
    return files


def build_plan(spec: dict, *, spec_path: Path) -> OnboardingPlan:
    meta_path = Path(spec["_meta_path"])
    org = spec["org"]
    client_id = spec["client_id"]
    forge_type = spec["forge"]["type"]

    plan = OnboardingPlan(
        spec_path=spec_path.resolve(),
        client_id=client_id,
        org=org,
        meta_repo=spec["meta_repo"],
        meta_path=meta_path,
        forge_type=forge_type,
    )

    skeleton = kit_root() / "examples" / "tenant-meta"
    if not skeleton.is_dir():
        plan.warnings.append(f"kit skeleton not found: {skeleton}")

    plan.create_dirs.append(str(meta_path))
    plan.create_files.append(f"{meta_path}/  (from {skeleton.name}/)")
    for rel in _config_files(org):
        plan.create_files.append(f"{meta_path}/{rel}")
    if spec["overrides"]["generate_playbook_hub"]:
        plan.create_files.append(f"{meta_path}/playbook/README.md")
    for rel in _template_files(spec):
        plan.create_files.append(f"{meta_path}/{rel}")
    plan.create_files.append(f"{meta_path}/.launchpad-version")

    if spec["registry"]["register_client"]:
        plan.patch_files.append(str(CLIENTS_FILE))
    if spec["registry"]["secrets_stub"]:
        plan.patch_files.append(str(ENV_D_DIR / f"{client_id}.env"))

    if forge_type == "gitlab":
        plan.warnings.append(
            "forge.type=gitlab: onboard apply scaffold is GitHub-first in v1; "
            "GitLab org config templates will be generated but setup-platform "
            "may require manual steps — see docs/multi-forge.md"
        )

    plan.manual_steps = [
        f"Create forge org/group `{org}` (admin access)",
        "Create private *-rules repos and tag initial refs before verify-harness",
        f"Paste forge token in {ENV_D_DIR / f'{client_id}.env'} (never commit)",
        f"Create remote `{org}/{spec['meta_repo']}` and push after apply",
    ]
    if forge_type == "github":
        plan.manual_steps.append(
            f"Create GitHub wiki Home page once — then launchpad publish-wiki --apply"
        )

    plan.next_commands = [
        f"launchpad onboard apply --spec {spec_path}",
        f"launchpad --client {client_id} doctor",
        f"launchpad --client {client_id} setup-platform --config config/platform-{org}.yaml --dry-run",
    ]
    if spec["provision"]["run_setup_platform"]:
        plan.next_commands.append(
            f"launchpad --client {client_id} setup-platform --config config/platform-{org}.yaml --apply"
        )
    for repo in spec["repos"][:2]:
        plan.next_commands.append(
            f"launchpad --client {client_id} sync-harness --repo {repo['name']} --dry-run"
        )

    if meta_path.is_dir():
        plan.warnings.append(f"meta path already exists: {meta_path} (apply will merge/update generated files)")

    return plan


def format_plan(plan: OnboardingPlan) -> str:
    lines = [
        "=== onboard plan ===",
        f"Spec:     {plan.spec_path}",
        f"Client:   {plan.client_id}",
        f"Org:      {plan.org}",
        f"Forge:    {plan.forge_type}",
        f"Meta:     {plan.meta_repo} → {plan.meta_path}",
        "",
    ]

    if plan.warnings:
        lines.append("Warnings:")
        for w in plan.warnings:
            lines.append(f"  • {w}")
        lines.append("")

    lines.append("Would create:")
    for item in plan.create_files:
        lines.append(f"  {item}")
    lines.append("")

    if plan.patch_files:
        lines.append("Would patch:")
        for item in plan.patch_files:
            lines.append(f"  {item}")
        lines.append("")

    lines.append("Manual (not executed by plan/apply):")
    for step in plan.manual_steps:
        lines.append(f"  • {step}")
    lines.append("")

    lines.append("Next commands:")
    for cmd in plan.next_commands:
        lines.append(f"  {cmd}")
    lines.append("")
    lines.append("[dry-run] no files written — run: launchpad onboard apply --spec …")

    return "\n".join(lines)
