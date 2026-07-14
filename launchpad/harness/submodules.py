"""Git submodule helpers shared by apply-harness."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_git(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _submodule_gitlink_in_index(repo_path: Path, submodule_rel: str) -> bool:
    result = run_git(["git", "ls-files", "-s", submodule_rel], cwd=repo_path)
    return result.returncode == 0 and result.stdout.strip().startswith("160000")


def _gitmodules_has_path(repo_path: Path, submodule_rel: str) -> bool:
    gitmodules = repo_path / ".gitmodules"
    if not gitmodules.is_file():
        return False
    return f"path = {submodule_rel}" in gitmodules.read_text(encoding="utf-8")


def _remove_broken_submodule(repo_path: Path, submodule_rel: str, *, label: str) -> None:
    """Drop a stale gitlink when .gitmodules or the checkout is missing."""
    print(f"  {label}: removing stale submodule gitlink for {submodule_rel} …")
    run_git(["git", "rm", "-rf", "--cached", submodule_rel], cwd=repo_path)
    dest = repo_path / submodule_rel
    if dest.exists() or dest.is_symlink():
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest, ignore_errors=True)
        else:
            dest.unlink(missing_ok=True)
    module_dir = repo_path / ".git" / "modules" / submodule_rel
    if module_dir.is_dir():
        shutil.rmtree(module_dir, ignore_errors=True)


def pin_git_ref(repo_dir: Path, ref: str, *, label: str = "") -> bool:
    """Fetch and force-checkout a tag or branch inside a git repo."""
    if not repo_dir.is_dir():
        return False

    prefix = f"  {label}: " if label else "  "
    print(f"{prefix}fetching {ref!r} …")

    fetch = run_git(
        ["git", "fetch", "origin", f"refs/tags/{ref}:refs/tags/{ref}"],
        cwd=repo_dir,
    )
    checkout_target = f"refs/tags/{ref}"
    if fetch.returncode != 0:
        fetch = run_git(["git", "fetch", "origin", ref], cwd=repo_dir)
        checkout_target = "FETCH_HEAD"
    if fetch.returncode != 0:
        print(f"  WARN: fetch {ref!r} failed: {fetch.stderr.strip()}", file=sys.stderr)
        return False

    print(f"{prefix}checkout {ref!r} …")
    # Detach at the exact fetched commit. Checking out a same-named local branch
    # can silently leave mutable branch pins behind origin/<ref>.
    checkout = run_git(
        ["git", "checkout", "--detach", "-f", checkout_target],
        cwd=repo_dir,
    )
    if checkout.returncode != 0:
        print(f"  WARN: checkout {ref!r} failed: {checkout.stderr.strip()}", file=sys.stderr)
        return False
    return True


def pin_submodule(
    repo_path: Path,
    submodule_rel: str,
    url: str,
    ref: str,
    *,
    label: str = "",
) -> bool:
    """Ensure submodule exists at repo_path/submodule_rel and pin it to ref."""
    if not (repo_path / ".git").is_dir():
        print(f"  WARN: {repo_path} is not a git repo — cannot pin submodule", file=sys.stderr)
        return False

    tag = label or submodule_rel
    submodule_dest = repo_path / submodule_rel
    registered = _gitmodules_has_path(repo_path, submodule_rel)
    gitlink = _submodule_gitlink_in_index(repo_path, submodule_rel)

    if gitlink and not registered:
        _remove_broken_submodule(repo_path, submodule_rel, label=tag)
        gitlink = False

    if registered and not submodule_dest.is_dir():
        print(f"  {tag}: submodule registered — initializing {submodule_rel} …")
        init = run_git(["git", "submodule", "update", "--init", "--force", submodule_rel], cwd=repo_path)
        if init.returncode != 0:
            print(f"  WARN: submodule init failed: {init.stderr.strip()}", file=sys.stderr)
            _remove_broken_submodule(repo_path, submodule_rel, label=tag)
            registered = False

    if not registered and not gitlink:
        print(f"  {tag}: adding submodule {url} → {submodule_rel} …")
        result = run_git(
            ["git", "submodule", "add", "--force", url, submodule_rel],
            cwd=repo_path,
        )
        if result.returncode != 0:
            print(f"  WARN: submodule add failed: {result.stderr.strip()}", file=sys.stderr)
            return False
    else:
        print(f"  {tag}: submodule exists — pinning {ref!r} …")

    if not pin_git_ref(submodule_dest, ref, label=tag):
        return False

    run_git(["git", "add", submodule_rel], cwd=repo_path)
    return True
