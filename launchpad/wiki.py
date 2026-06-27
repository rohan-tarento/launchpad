"""Publish wiki/*.md to a GitHub Wiki repository (git push)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from launchpad.config import load_wiki_config, tenant_root


class WikiError(RuntimeError):
    pass


def _token() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
    if not token:
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                check=True,
            )
            token = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    if not token:
        raise WikiError(
            "GITHUB_TOKEN not set and gh auth token failed. "
            "Set GITHUB_TOKEN in .env or run: gh auth login"
        )
    return token


def run(
    *,
    config_path: str | None = None,
    org: str = "",
    dry_run: bool = True,
) -> None:
    """Publish wiki/*.md to GitHub Wiki. dry_run=True prints actions only."""
    if not config_path:
        raise WikiError("config_path is required (pass --config or --org)")
    cfg_path = Path(config_path)
    cfg = load_wiki_config(cfg_path)

    org = org or cfg["org"]
    repo = cfg["repo"]
    if not org or not repo:
        raise WikiError("org and repo are required in WikiConfig")

    wiki_dir_raw = cfg.get("wiki_dir", "wiki")
    wiki_dir = Path(wiki_dir_raw)
    if not wiki_dir.is_absolute():
        wiki_dir = (tenant_root() / wiki_dir_raw).resolve()

    if not wiki_dir.is_dir():
        raise WikiError(f"wiki dir not found: {wiki_dir}")

    md_files = sorted(wiki_dir.glob("*.md"))
    if not md_files:
        raise WikiError(f"no *.md files found in {wiki_dir}")

    author_name = cfg.get("commit_author_name", "launchpad")
    author_email = cfg.get("commit_author_email", "launchpad@localhost")
    commit_msg = (cfg.get("commit_message") or "").strip()
    if not commit_msg:
        commit_msg = f"chore: publish wiki from {repo}/wiki/"
    github_host = os.environ.get("GITHUB_HOST", "github.com")
    wiki_url = f"https://{github_host}/{org}/{repo}/wiki"

    print("=== publish-wiki ===")
    print(f"Config:   {cfg_path}")
    print(f"Org:      {org}")
    print(f"Repo:     {repo}")
    print(f"Wiki dir: {wiki_dir} ({len(md_files)} .md file(s))")
    print(f"Remote:   https://{github_host}/{org}/{repo}.wiki.git")
    print(f"Mode:     {'dry-run' if dry_run else 'apply'}")
    print("")

    if dry_run:
        print("Files that would be published:")
        for f in md_files:
            print(f"  {f.name}")
        print("")
        print("[dry-run] would clone wiki repo, copy files, commit, and push")
        return

    token = _token()
    auth_remote = (
        f"https://x-access-token:{token}@{github_host}/{org}/{repo}.wiki.git"
    )

    try:
        subprocess.run(
            ["git", "ls-remote", auth_remote, "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        raise WikiError(
            f"Wiki git repo not accessible: https://{github_host}/{org}/{repo}.wiki.git\n\n"
            "GitHub creates the wiki repo only after you save the first page in the browser.\n"
            "One-time setup:\n"
            f"  1. Open https://{github_host}/{org}/{repo}/wiki\n"
            "  2. Click 'Create the first page'\n"
            "  3. Title: Home  →  paste wiki/Home.md content  →  Save Page\n"
            "  4. Re-run: launchpad publish-wiki --apply\n\n"
            "Full guide: playbook/wiki-setup.md"
        )

    with tempfile.TemporaryDirectory() as tmp:
        clone_dir = Path(tmp) / "wiki"
        subprocess.run(
            ["git", "clone", auth_remote, str(clone_dir), "--quiet"],
            check=True,
        )

        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=clone_dir,
            capture_output=True,
            text=True,
        )
        branch = result.stdout.strip() or "master"

        for md_file in md_files:
            shutil.copy2(md_file, clone_dir / md_file.name)

        subprocess.run(["git", "add", "-A"], cwd=clone_dir, check=True)

        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=clone_dir,
        )
        if diff.returncode == 0:
            print("Wiki already up to date.")
            return

        subprocess.run(
            [
                "git",
                "-c", f"user.email={author_email}",
                "-c", f"user.name={author_name}",
                "commit",
                "-m", commit_msg,
            ],
            cwd=clone_dir,
            check=True,
        )
        subprocess.run(
            ["git", "push", "origin", branch],
            cwd=clone_dir,
            check=True,
        )
        print(f"Published → {wiki_url}")
