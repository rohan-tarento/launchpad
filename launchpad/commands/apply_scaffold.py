"""apply-scaffold — run cookiecutter scaffold from scaffold-<org>.yaml.

Reads scaffold-<org>.yaml ONLY.
Context is passed free-form to cookiecutter — no kit-owned key validation.
Template owners can evolve their cookiecutter.json without Launchpad changes.

Usage:
  launchpad apply-scaffold --meta [--apply] [--force]
  launchpad apply-scaffold --repo <name> [--apply] [--force]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from launchpad.schema import SchemaError
from launchpad.schema.scaffold import ScaffoldEntry, ScaffoldSchema, load_scaffold


def _find_config(config_dir: Path, pattern: str) -> Path | None:
    matches = list(config_dir.glob(pattern))
    return matches[0] if matches else None


def _scaffold_target_dir(
    ws: Path,
    *,
    meta: bool,
    repo_name: str,
    prog: object | None,
    entry: ScaffoldEntry,
) -> Path:
    """Directory cookiecutter will write into (workspace / project folder)."""
    if meta:
        if prog is not None and hasattr(prog, "meta_repo"):
            return ws / str(getattr(prog, "meta_repo"))
        meta_repo = entry.context.get("meta_repo")
        if meta_repo:
            return ws / str(meta_repo)
        return ws
    return ws / repo_name


def _print_exists_hint(
    *,
    target: Path,
    meta: bool,
    repo_name: str,
) -> None:
    client_id = os.environ.get("LAUNCHPAD_CLIENT", "").strip()
    client_prefix = f"--client {client_id} " if client_id else ""
    target_flag = "--meta" if meta else f"--repo {repo_name}"
    print(f"ERROR: output directory already exists: {target}", file=sys.stderr)
    print(
        "  Normal after init-client — the local clone is already there.",
        file=sys.stderr,
    )
    print(
        "  Re-run with --force to overlay the foundation template "
        "(keeps .git; does not delete local-only files):",
        file=sys.stderr,
    )
    print(
        f"  launchpad {client_prefix}apply-scaffold {target_flag} --apply --force",
        file=sys.stderr,
    )


def _resolve_template_url(entry: ScaffoldEntry) -> str:
    """Resolve template shorthand to a clonable URL."""
    t = entry.template
    if t.startswith("gh:"):
        slug = t[3:]
        return f"https://github.com/{slug}"
    return t


def _run_cookiecutter(
    template_url: str,
    ref: str,
    context: dict,
    *,
    output_dir: Path,
    force: bool = False,
) -> None:
    """Invoke cookiecutter against the template."""
    try:
        from cookiecutter.main import cookiecutter
    except ImportError:
        raise RuntimeError("cookiecutter is not installed.  Run: pip install cookiecutter")

    cookiecutter(
        template_url,
        checkout=ref,
        no_input=True,
        extra_context=context,
        output_dir=str(output_dir),
        overwrite_if_exists=force,
    )


def run_apply_scaffold(
    *,
    meta: bool = False,
    repo_name: str = "",
    apply: bool = False,
    force: bool = False,
    config_dir: Path | None = None,  # None only in tests — main() always resolves via clients.yaml
) -> int:
    if not meta and not repo_name:
        print("ERROR: pass --meta or --repo <name>", file=sys.stderr)
        return 1

    if config_dir is None:
        # Should not reach here — main() blocks client-less commands early.
        raise RuntimeError("config_dir not resolved — pass --client <id> or run launchpad onboard interview")
    cdir = config_dir

    sca_path = _find_config(cdir, "scaffold-*.yaml")
    if sca_path is None:
        print(f"ERROR: scaffold-<org>.yaml not found in {cdir}", file=sys.stderr)
        print("  Run 'launchpad onboard interview' first", file=sys.stderr)
        return 1

    try:
        sca = load_scaffold(sca_path)
    except SchemaError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    prog = None
    try:
        prog_path = cdir / "programme.yaml"
        if prog_path.is_file():
            from launchpad.schema.programme import load_programme
            prog = load_programme(prog_path)
            workspace = prog.workspace
        else:
            workspace = Path(".").resolve().parent
    except SchemaError:
        workspace = Path(".").resolve().parent

    ws = Path(workspace).expanduser().resolve()

    if meta:
        entry = sca.meta
        if entry is None:
            print("ERROR: scaffold-<org>.yaml has no 'meta' block", file=sys.stderr)
            return 1
        label = "meta"
        output_dir = ws
    else:
        if repo_name not in sca.repos:
            print(f"ERROR: repo '{repo_name}' not in scaffold-<org>.yaml repos", file=sys.stderr)
            print(f"  Known repos: {sorted(sca.repos)}", file=sys.stderr)
            return 1
        entry = sca.repos[repo_name]
        label = repo_name
        output_dir = ws

    if not entry.enabled:
        print(f"  scaffold.{label}.enabled = false — nothing to do.")
        print(f"  Enable it in {sca_path.name} and re-run.")
        return 0

    template_url = _resolve_template_url(entry)
    ref = entry.ref
    context = entry.context

    print(f"apply-scaffold  →  {label}")
    print(f"  template:  {entry.template}")
    print(f"  ref:       {ref}")
    print(f"  context:   {context}")
    print(f"  output:    {output_dir}")
    print()

    if not apply:
        print("  [dry-run] No files written.  Pass --apply to execute.")
        print()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  NEXT:                                                       ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        target_flag = "--meta" if meta else f"--repo {repo_name}"
        print(f"║  launchpad apply-scaffold {target_flag} --apply{'':<30}  ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        return 0

    target_dir = _scaffold_target_dir(
        ws, meta=meta, repo_name=repo_name, prog=prog, entry=entry
    )
    if target_dir.is_dir() and not force:
        _print_exists_hint(target=target_dir, meta=meta, repo_name=repo_name)
        return 1

    try:
        _run_cookiecutter(template_url, ref, context, output_dir=output_dir, force=force)
    except Exception as exc:
        if not force and "already exists" in str(exc).lower():
            _print_exists_hint(target=target_dir, meta=meta, repo_name=repo_name)
            return 1
        print(f"ERROR: cookiecutter failed: {exc}", file=sys.stderr)
        return 1

    # Marker for status — records which foundation was applied
    marker_repo = ws / (prog.meta_repo if meta and prog else repo_name)
    marker_path = marker_repo / ".launchpad-scaffold"
    marker_path.write_text(
        f"template: {entry.template}\nref: {ref}\n",
        encoding="utf-8",
    )
    print(f"  ✔  scaffold applied → {marker_repo}")
    print()

    client_id = os.environ.get("LAUNCHPAD_CLIENT", "").strip()
    client_prefix = f"--client {client_id} " if client_id else ""
    target_flag = "--meta" if meta else f"--repo {repo_name}"
    if meta:
        next_cmd = f"launchpad {client_prefix}apply-harness --meta --apply"
    else:
        next_cmd = f"launchpad {client_prefix}apply-harness --repo {repo_name} --apply"

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  NEXT:                                                       ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  {next_cmd:<60}  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    return 0
