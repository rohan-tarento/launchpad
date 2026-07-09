"""Greenfield onboard interview — 4 questions, auto-applies locally.

Flow:
  1. Ask: programme name (human, e.g. "STRATUM")
  2. Derive programme_slug, show it, confirm or override
  3. Ask: GitHub org (exact spelling, e.g. "Sandvik-Common")
  4. Ask: workspace path (where meta repo will be cloned)

After the 4 questions:
  • Creates <workspace>/<slug>-meta/config/ with all 5 YAML files
  • Patches ~/.config/launchpad/clients.yaml
  • Writes env.d/<slug>.env stub with GitHub PAT instructions
  • Prints a single NEXT: step
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Callable, TextIO

import yaml

from launchpad.clients import CLIENTS_FILE, CONFIG_DIR, ENV_D_DIR
from launchpad.onboarding.errors import OnboardingError
from launchpad.schema.governance import STARTER_STACKS

_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")


# ─── Prompt helpers ─────────────────────────────────────────────────────────


def _ask(
    label: str,
    default: str = "",
    *,
    required: bool = True,
    input_fn: Callable[[str], str] | None = None,
    out: TextIO = sys.stdout,
) -> str:
    reader = input_fn or input
    hint = f" [{default}]" if default else ""
    while True:
        value = reader(f"  {label}{hint}: ").strip()
        if not value:
            if default:
                return default
            if required:
                out.write("    (required)\n")
                continue
            return ""
        return value


def _ask_slug(
    label: str,
    default: str = "",
    *,
    input_fn: Callable[[str], str] | None = None,
    out: TextIO = sys.stdout,
) -> str:
    reader = input_fn or input
    while True:
        hint = f" [{default}]" if default else ""
        value = reader(f"  {label}{hint}: ").strip() or default
        if not value:
            out.write("    (required)\n")
            continue
        if not _SLUG_RE.match(value):
            out.write("    Must be lowercase [a-z][a-z0-9-]+\n")
            continue
        return value


def _derive_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ─── 5-YAML renderer ────────────────────────────────────────────────────────


def _render_programme(slug: str, programme: str, org: str, workspace: str, meta_repo: str) -> str:
    return f"""\
apiVersion: launchpad/v1
kind: Programme
programme: {programme}
programme_slug: {slug}
org: {org}
meta_repo: {meta_repo}
workspace: {workspace}
forge:
  provider: github
"""


def _render_governance(org: str, meta_repo: str) -> str:
    stacks_block = "\n".join(f"  # {k}: {v}" for k, v in STARTER_STACKS.items())
    return f"""\
apiVersion: launchpad/v1
kind: GovernanceConfig

# Day 1: meta repo only.
# Add app repos incrementally (Day N) by uncommenting / adding repo blocks.
org: {org}

stack_profiles:
  # Starter stacks are always available — list here for reference only.
{stacks_block}
  #
  # Add custom stacks:
  # go-backend: Go microservice

teams:
  - name: platform-core
    description: Platform owners
    privacy: closed

repos:
  {meta_repo}:
    stack: meta-pm
    teams: [platform-core]
    visibility: private
    description: Control-plane for {org}

policy:
  default_branch: main
  require_pr_reviews: 1
  dismiss_stale_reviews: true

project_board:
  enabled: true
  name: "{org} Board"
"""


def _render_harness(org: str) -> str:
    return f"""\
apiVersion: launchpad/v1
kind: HarnessConfig
org: {org}

# One profile entry per stack you use.
# constitution.ref must be a pinned tag — change it here to upgrade rules.
#
# codeowners_template: filename inside kit templates/ to seed as .github/CODEOWNERS
#   Default convention: CODEOWNERS.<profile-name>  (e.g. CODEOWNERS.python-backend)
#
# harness_pin_template: filename inside kit templates/ to seed as .harness-pin.yaml
#   Default convention: harness-pin.<profile-name>.yaml
#
# Both fields are optional — omit to use the convention-based default.
profiles:
  meta-pm:
    # constitution: omitted — meta repos hold config/planning docs, not code.
    # No .cursor/rules submodule is needed here.
    skills: []
    codeowners_template: CODEOWNERS.meta-pm
    harness_pin_template: harness-pin.meta.yaml

  python-backend:
    constitution:
      repo: python-services-rules
      ref: v2.1.0
    skills:
      - repo: python-agent-skills
        ref: v1.0.0
    codeowners_template: CODEOWNERS.python-backend
    harness_pin_template: harness-pin.python-backend.yaml

  # nextjs-frontend:
  #   constitution:
  #     repo: nextjs-frontend-rules
  #     ref: v1.0.0
  #   skills: []
  #   codeowners_template: CODEOWNERS.nextjs-frontend
  #   harness_pin_template: harness-pin.nextjs-frontend.yaml

  # terraform-iac:
  #   constitution:
  #     repo: terraform-rules
  #     ref: v1.0.0
  #   skills: []
  #   codeowners_template: CODEOWNERS.terraform-iac
  #   harness_pin_template: harness-pin.terraform-iac.yaml

# Per-repo harness_profile overrides (optional).
# If absent, a repo's harness_profile defaults to its stack from governance.yaml.
repos: {{}}
"""


def _render_scaffold(org: str) -> str:
    return f"""\
apiVersion: launchpad/v1
kind: ScaffoldConfig

# Scaffold is optional and entirely YAML-driven.
# Enable a block and fill in template + ref + context, then run:
#   launchpad apply-scaffold --meta --apply
org: {org}

meta:
  enabled: false
  engine: cookiecutter
  # template: gh:drivestream-lab/tenant-meta-foundation
  # ref: v0.1.0
  # context:
  #   project_name: {org}
  #   programme_slug: <slug>
  #   github_org: {org}

# App repos — add a block for each repo when you are ready to scaffold.
repos: {{}}

  # Example (copy-paste and uncomment):
  # <repo-name>:
  #   enabled: true
  #   engine: cookiecutter
  #   template: gh:drivestream-lab/python-fastapi-foundation
  #   ref: v0.3.0
  #   context:
  #     project_name: <repo-name>
  #     has_kafka: false
  #     has_postgres: true
"""


def _render_catalog(org: str, meta_repo: str) -> str:
    return f"""\
apiVersion: launchpad/v1
kind: ServiceCatalog

# Required — at least one service must be listed.
# Day 1: only the meta repo is live.
# Promote app repos from 'planned' to 'live' once they are scaffolded.
org: {org}

services:
  {meta_repo}:
    stack: meta-pm
    description: Control-plane for {org}
    status: live
    teams: [platform-core]
    links:
      repo: https://github.com/{org}/{meta_repo}

  # ─── Day-N examples (uncomment when the repo is live) ───────────────────
  #
  # <slug>-platform-core:
  #   stack: python-backend
  #   description: Core platform microservice
  #   status: planned
  #   teams: [platform-core]
  #
  # <slug>-web:
  #   stack: nextjs-frontend
  #   description: Web UI
  #   status: planned
  #   teams: [platform-core]
  #
  # <slug>-infra:
  #   stack: terraform-iac
  #   description: Terraform infrastructure modules
  #   status: planned
  #   teams: [platform-core]
"""


# ─── Registry helpers ────────────────────────────────────────────────────────


def _patch_clients_yaml(slug: str, meta_path: Path) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CLIENTS_FILE.is_file():
        with CLIENTS_FILE.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    if not isinstance(data, dict):
        data = {}
    clients: list[dict[str, Any]] = data.get("clients") or []
    if not isinstance(clients, list):
        clients = []

    entry = {"id": slug, "path": str(meta_path), "forge": "github"}
    clients = [c for c in clients if not (isinstance(c, dict) and c.get("id") == slug)]
    clients.append(entry)
    data["clients"] = clients

    with CLIENTS_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)


def _write_env_stub(slug: str, org: str, meta_path: Path) -> Path:
    ENV_D_DIR.mkdir(parents=True, exist_ok=True)
    path = ENV_D_DIR / f"{slug}.env"
    if path.is_file():
        return path
    path.write_text(
        f"# {slug} factory secrets\n"
        f"# ─────────────────────────────────────────────────────────────────\n"
        f"# 1. Create a GitHub PAT with these scopes:\n"
        f"#      repo, admin:org, project, delete_repo\n"
        f"#    (GitHub → Settings → Developer settings → Personal access tokens → Fine-grained)\n"
        f"# 2. Paste the token below (replace github_pat_REPLACE_ME)\n"
        f"# 3. Save, then run:  chmod 600 {path}\n"
        f"# ─────────────────────────────────────────────────────────────────\n"
        f"GITHUB_TOKEN=github_pat_REPLACE_ME\n"
        f"\n"
        f"# GitHub org:  {org}\n"
        f"# Meta repo:   https://github.com/{org}/{slug}-meta\n"
        f"\n"
        f"# export LAUNCHPAD_TENANT_ROOT={meta_path}\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    return path


# ─── Public entry point ──────────────────────────────────────────────────────


def run_interview(
    *,
    input_fn: Callable[[str], str] | None = None,
    out: TextIO = sys.stdout,
) -> None:
    """Run the 4-question interview, write config files, patch registry, print NEXT."""
    out.write("\n")
    out.write("╔══════════════════════════════════════════╗\n")
    out.write("║   launchpad — onboard interview          ║\n")
    out.write("╚══════════════════════════════════════════╝\n")
    out.write("\n")
    out.write("This sets up your programme locally in 4 questions.\n")
    out.write("All config files are created in your meta repo.\n\n")

    # Q1: Programme name
    programme = _ask("Programme name  (e.g. STRATUM)", input_fn=input_fn, out=out)

    # Q2: Confirm slug (auto-derived)
    derived = _derive_slug(programme)
    out.write(f"\n  Auto-derived slug: {derived}\n")
    slug = _ask_slug(
        "Programme slug  (confirm or override)",
        derived,
        input_fn=input_fn,
        out=out,
    )

    # Q3: GitHub org
    out.write("\n  GitHub org — the exact organisation slug on GitHub.\n")
    out.write("  Example: Sandvik-Common, acme-corp, my-startup\n")
    org = _ask("GitHub org", input_fn=input_fn, out=out)

    # Q4: Workspace
    default_ws = str(Path("~/Workspace").expanduser())
    out.write(f"\n  Parent directory where your meta repo will live.\n")
    workspace = _ask("Workspace path", default_ws, input_fn=input_fn, out=out)

    meta_repo = f"{slug}-meta"
    meta_path = Path(workspace).expanduser().resolve() / meta_repo
    config_dir = meta_path / "config"

    out.write("\n")
    out.write("─" * 50 + "\n")
    out.write(f"  programme:       {programme}\n")
    out.write(f"  slug:            {slug}\n")
    out.write(f"  org:             {org}\n")
    out.write(f"  meta repo:       {meta_repo}\n")
    out.write(f"  local path:      {meta_path}\n")
    out.write("─" * 50 + "\n\n")

    # Write config files
    config_dir.mkdir(parents=True, exist_ok=True)

    files: dict[str, str] = {
        "programme.yaml": _render_programme(slug, programme, org, workspace, meta_repo),
        f"governance-{org}.yaml": _render_governance(org, meta_repo),
        f"harness-{org}.yaml": _render_harness(org),
        f"scaffold-{org}.yaml": _render_scaffold(org),
        f"service-catalog-{org}.yaml": _render_catalog(org, meta_repo),
    }

    for filename, content in files.items():
        fpath = config_dir / filename
        if not fpath.exists():
            fpath.write_text(content, encoding="utf-8")
            out.write(f"  ✔  {fpath.relative_to(meta_path)}\n")
        else:
            out.write(f"  –  {fpath.relative_to(meta_path)}  (already exists, skipped)\n")

    # Patch registry
    _patch_clients_yaml(slug, meta_path)
    out.write(f"\n  ✔  ~/.config/launchpad/clients.yaml  (id: {slug})\n")

    env_path = _write_env_stub(slug, org, meta_path)
    out.write(f"  ✔  {env_path}  (PAT stub)\n")

    out.write("\n")
    out.write("╔══════════════════════════════════════════════════════════════╗\n")
    out.write("║  NEXT:                                                       ║\n")
    out.write("╠══════════════════════════════════════════════════════════════╣\n")
    out.write(f"║  1. Open:  {str(env_path):<50}  ║\n")
    out.write( "║     Replace github_pat_REPLACE_ME with your GitHub PAT      ║\n")
    out.write(f"║     Scopes: repo, admin:org, project                        ║\n")
    out.write( "║                                                              ║\n")
    out.write(f"║  2. chmod 600 {str(env_path):<47}  ║\n")
    out.write( "║                                                              ║\n")
    out.write(f"║  3. launchpad --client {slug} doctor                         ║\n")
    out.write("╚══════════════════════════════════════════════════════════════╝\n")
    out.write("\n")
