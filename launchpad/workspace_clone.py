"""Clone gitflow repos locally so scaffold, sync-harness, and gitflow templates can run immediately."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from launchpad.config import load_gitflow_config, resolve_config_path, resolve_workspace_parent, tenant_root
from launchpad.github_ops import repo_exists
from launchpad.repo_seed import factory_app_repo_names


class WorkspaceCloneError(RuntimeError):
    """One or more repos could not be cloned or linked locally."""


def github_https_url(org: str, repo: str) -> str:
    return f"https://github.com/{org}/{repo}.git"


def repo_dest_path(
    repo: str,
    *,
    workspace_parent: Path,
    meta_repo: str,
) -> Path:
    if repo == meta_repo or repo == tenant_root().name:
        return tenant_root()
    return workspace_parent / repo


def _run_git(args: list[str], *, cwd: Path, dry_run: bool) -> None:
    cmd = ["git", *args]
    if dry_run:
        print(f"  [dry-run] {' '.join(cmd)}  (cwd={cwd})")
        return
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise WorkspaceCloneError(
            f"git {' '.join(args)} failed in {cwd}" + (f": {err}" if err else "")
        )


def _clone_fresh(*, url: str, branch: str, dest: Path, dry_run: bool) -> None:
    if dest.exists():
        if dest.is_dir() and not any(dest.iterdir()):
            if not dry_run:
                dest.rmdir()
        elif dest.is_dir():
            raise WorkspaceCloneError(
                f"{dest} exists and is not empty — remove it or use an existing git checkout"
            )
        else:
            raise WorkspaceCloneError(f"{dest} exists and is not a directory")
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[clone] {url} @ {branch} → {dest}")
    _run_git(["clone", "--branch", branch, url, str(dest)], cwd=dest.parent, dry_run=dry_run)


def _link_existing(*, url: str, branch: str, dest: Path, dry_run: bool) -> None:
    print(f"[link] {dest} → {url} @ {branch} (existing directory)")
    _run_git(["init"], cwd=dest, dry_run=dry_run)
    if dry_run:
        _run_git(["remote", "add", "origin", url], cwd=dest, dry_run=True)
        _run_git(["fetch", "origin", branch], cwd=dest, dry_run=True)
        _run_git(["checkout", "-B", branch], cwd=dest, dry_run=True)
        _run_git(
            ["merge", f"origin/{branch}", "--allow-unrelated-histories", "-m", "launchpad: merge remote develop"],
            cwd=dest,
            dry_run=True,
        )
        return

    proc = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=dest,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        _run_git(["remote", "add", "origin", url], cwd=dest, dry_run=False)
    else:
        _run_git(["remote", "set-url", "origin", url], cwd=dest, dry_run=False)

    status = subprocess.run(["git", "status", "--porcelain"], cwd=dest, capture_output=True, text=True)
    if status.returncode == 0 and status.stdout.strip():
        _run_git(["add", "-A"], cwd=dest, dry_run=False)
        _run_git(["commit", "-m", "chore: local content before linking remote develop"], cwd=dest, dry_run=False)

    _run_git(["fetch", "origin", branch], cwd=dest, dry_run=False)
    _run_git(["checkout", "-B", branch], cwd=dest, dry_run=False)
    _run_git(
        [
            "merge",
            f"origin/{branch}",
            "--allow-unrelated-histories",
            "-m",
            "chore: merge factory develop seed",
        ],
        cwd=dest,
        dry_run=False,
    )


def clone_one_repo(
    *,
    org: str,
    repo: str,
    dest: Path,
    branch: str = "develop",
    dry_run: bool,
    check_remote: bool = True,
    client: Any | None = None,
) -> None:
    url = github_https_url(org, repo)

    if (dest / ".git").exists():
        print(f"[skip] {dest} — already a git checkout")
        return

    if check_remote and client is not None and not client.dry_run:
        if not repo_exists(client, org, repo):
            raise WorkspaceCloneError(f"{org}/{repo} not found on GitHub — run bootstrap-org first")

    if dest.exists() and dest.is_dir() and any(dest.iterdir()):
        _link_existing(url=url, branch=branch, dest=dest, dry_run=dry_run)
        return

    _clone_fresh(url=url, branch=branch, dest=dest, dry_run=dry_run)


def meta_repo_name(cfg: dict[str, Any]) -> str:
    app_repos = factory_app_repo_names(cfg)
    meta_candidates = [r["name"] for r in cfg.get("repos") or [] if r["name"] not in app_repos]
    if len(meta_candidates) == 1:
        return meta_candidates[0]
    if tenant_root().name in {r["name"] for r in cfg.get("repos") or []}:
        return tenant_root().name
    return meta_candidates[0] if meta_candidates else tenant_root().name


def run(
    client: Any,
    *,
    org: str = "",
    config_path: Path | str | None = None,
    filter_repo: str = "",
    branch: str = "develop",
) -> None:
    cfg_path = resolve_config_path("gitflow", org=org, explicit=config_path)
    cfg = load_gitflow_config(cfg_path)
    org = org or cfg["org"]
    workspace_parent = resolve_workspace_parent(gitflow_options=cfg.get("options") or {})
    meta = meta_repo_name(cfg)
    dry_run = bool(getattr(client, "dry_run", True))

    print("=== clone-repos ===")
    print(f"Org: {org}")
    print(f"Config: {cfg_path}")
    print(f"Workspace parent: {workspace_parent}")
    print(f"Tenant meta: {tenant_root()} ({meta})")
    print(f"Branch: {branch}")
    print(f"Mode: {'dry-run' if dry_run else 'apply'}")
    print("")

    errors: list[str] = []
    for repo_entry in cfg.get("repos") or []:
        repo = str(repo_entry["name"])
        if filter_repo and repo != filter_repo:
            continue
        dest = repo_dest_path(repo, workspace_parent=workspace_parent, meta_repo=meta)
        kind = "meta" if repo == meta or dest == tenant_root() else "app"
        print(f"--- {org}/{repo} ({kind}) → {dest} ---")
        try:
            clone_one_repo(
                org=org,
                repo=repo,
                dest=dest,
                branch=branch,
                dry_run=dry_run,
                client=client,
            )
        except WorkspaceCloneError as exc:
            print(f"[FAIL] {exc}")
            errors.append(str(exc))
        except Exception as exc:
            print(f"[FAIL] {org}/{repo}: {exc}")
            errors.append(f"{org}/{repo}: {exc}")
        print("")

    if errors:
        print("=== clone-repos: FAILED ===")
        raise WorkspaceCloneError(
            f"{len(errors)} repo(s) not cloned — fix errors above and re-run clone-repos --apply"
        )

    print("=== Done ===")
    if dry_run:
        print("Re-run with --apply to clone/link local checkouts.")
    else:
        print("Local clones ready — scaffold, sync-harness, and gitflow templates can run offline.")
