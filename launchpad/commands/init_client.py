"""init-client — Day-1 setup for a programme (meta repo) or Day-N repo.

Pipeline (for --meta):
  1. Validate programme.yaml + governance-<org>.yaml
  2. Ensure GitHub team(s) declared for the meta repo
  3. Ensure the meta repo on GitHub
  4. Assign teams to repo
  5. Setup gitflow (default branch + branch protection)
  6. Ensure project board + link repo
  7. Merge service-catalog repo entry
  8. Re-ensure clients.yaml entry from programme.yaml
  9. Print NEXT: block

Pipeline (for --repo <name>):
  1. Validate programme.yaml + governance-<org>.yaml
  2. Ensure GitHub team(s) declared for the repo
  3. Ensure the app repo on GitHub
  4. Assign teams to repo
  5. Setup gitflow
  6. Link repo to project board
  7. Merge service-catalog repo entry
  8. Print NEXT: block

All steps are idempotent — re-run after a config fix with the same flags.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from launchpad.schema import SchemaError
from launchpad.schema.catalog import load_catalog
from launchpad.schema.governance import load_governance
from launchpad.schema.programme import load_programme
from launchpad.clients import CLIENTS_FILE, CONFIG_DIR


def _find_config(config_dir: Path, pattern: str) -> Path | None:
    matches = list(config_dir.glob(pattern))
    return matches[0] if matches else None


def _load_all_schemas(config_dir: Path) -> tuple[Any, Any, Any]:
    prog_path = config_dir / "programme.yaml"
    if not prog_path.is_file():
        raise SchemaError(
            f"programme.yaml not found in {config_dir}",
            hint="Run 'launchpad onboard interview' first",
        )
    prog = load_programme(prog_path)

    gov_path = _find_config(config_dir, f"governance-*.yaml")
    if gov_path is None:
        raise SchemaError(
            f"governance-<org>.yaml not found in {config_dir}",
            hint="Run 'launchpad onboard interview' first",
        )
    gov = load_governance(gov_path)

    cat_path = _find_config(config_dir, f"service-catalog-*.yaml")
    if cat_path is None:
        raise SchemaError(
            f"service-catalog-<org>.yaml not found in {config_dir}",
            hint="Run 'launchpad onboard interview' first",
        )
    cat = load_catalog(cat_path)

    return prog, gov, cat


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


def run_init_client(
    *,
    meta: bool = False,
    repo_name: str = "",
    apply: bool = False,
    dry_run: bool = True,
    config_dir: Path | None = None,
) -> int:
    if not meta and not repo_name:
        print("ERROR: pass --meta or --repo <name>", file=sys.stderr)
        return 1

    cdir = config_dir or (Path(".").resolve() / "config")

    try:
        prog, gov, cat = _load_all_schemas(cdir)
    except SchemaError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    org = prog.org
    slug = prog.programme_slug
    dr = dry_run or not apply

    from launchpad.forge.providers.github import GitHubForgeProvider

    targets: list[str] = []
    if meta:
        targets = [prog.meta_repo]
    else:
        if repo_name not in gov.repos:
            print(f"ERROR: repo '{repo_name}' is not declared in governance-{org}.yaml", file=sys.stderr)
            print(f"  Known repos: {sorted(gov.repos)}", file=sys.stderr)
            return 1
        targets = [repo_name]

    policy = gov.policy
    required_approvals = int(policy.get("require_pr_reviews", 1))
    dismiss_stale = bool(policy.get("dismiss_stale_reviews", True))
    default_branch = str(policy.get("default_branch", "main"))

    with GitHubForgeProvider(dry_run=dr) as forge:
        # Ensure project board (for all targets, use a shared board)
        board_id = ""
        if gov.project_board.get("enabled"):
            board_name = str(gov.project_board.get("name", f"{org} Board"))
            if not dr:
                print(f"  Ensuring project board: {board_name}")
            board_id = forge.ensure_project_board(org, board_name)

        for target_repo in targets:
            repo_cfg = gov.repos.get(target_repo)
            if repo_cfg is None:
                print(f"  WARN: {target_repo} not in governance — skipping", file=sys.stderr)
                continue

            print(f"\ninit-client  →  {org}/{target_repo}")

            # 1. Teams
            for team_name in repo_cfg.teams:
                team_entry = next((t for t in gov.teams if t.name == team_name), None)
                desc = team_entry.description if team_entry else ""
                privacy = team_entry.privacy if team_entry else "closed"
                forge.ensure_team(org, team_name, description=desc, privacy=privacy)

            # 2. Repo
            forge.ensure_repo(
                org,
                target_repo,
                description=repo_cfg.description,
                visibility=repo_cfg.visibility,
            )

            # 3. Assign teams
            for team_name in repo_cfg.teams:
                forge.add_team_to_repo(org, target_repo, team_name)

            # 4. Gitflow
            forge.ensure_default_branch(org, target_repo, default_branch)
            forge.ensure_branch_protection(
                org,
                target_repo,
                default_branch,
                required_approvals=required_approvals,
                dismiss_stale=dismiss_stale,
            )

            # 5. Link to board
            if board_id:
                forge.link_repo_to_project(org, target_repo, board_id)

    # 6. Re-ensure clients.yaml (meta only)
    if meta:
        meta_path = Path(prog.workspace).expanduser().resolve() / prog.meta_repo
        _patch_clients_yaml(slug, meta_path)
        if dr:
            print(f"  [dry-run] ensure clients.yaml entry: id={slug}")
        else:
            print(f"  ✔  ~/.config/launchpad/clients.yaml  (id={slug})")

    # NEXT step
    print()
    if meta:
        from launchpad.schema.scaffold import load_scaffold

        sca_path = _find_config(cdir, "scaffold-*.yaml")
        scaffold_enabled = False
        if sca_path and sca_path.is_file():
            try:
                from launchpad.schema.scaffold import ScaffoldSchema
                sca = load_scaffold(sca_path)
                scaffold_enabled = sca.meta is not None and sca.meta.enabled
            except SchemaError:
                pass

        if scaffold_enabled:
            next_cmd = f"launchpad apply-scaffold --meta --apply"
        else:
            next_cmd = f"launchpad apply-scaffold --meta --apply  # (after enabling meta scaffold in config/scaffold-{org}.yaml)"

        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  NEXT:                                                       ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  {next_cmd:<60}  ║")
        print("╚══════════════════════════════════════════════════════════════╝")
    else:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  NEXT:                                                       ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  launchpad apply-harness --repo {repo_name:<29}  ║")
        print("╚══════════════════════════════════════════════════════════════╝")

    return 0
