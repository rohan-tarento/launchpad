"""apply-scaffold — run cookiecutter scaffold from scaffold-<org>.yaml.

Reads scaffold-<org>.yaml ONLY.
Context is passed free-form to cookiecutter — no kit-owned key validation.
Template owners can evolve their cookiecutter.json without Launchpad changes.

Usage:
  launchpad apply-scaffold --meta [--apply] [--force]
  launchpad apply-scaffold --repo <name> [--apply] [--force]
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from launchpad.schema import SchemaError
from launchpad.schema.scaffold import ScaffoldEntry, ScaffoldSchema, load_scaffold


def _find_config(config_dir: Path, pattern: str) -> Path | None:
    matches = list(config_dir.glob(pattern))
    return matches[0] if matches else None


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
    config_dir: Path | None = None,
) -> int:
    if not meta and not repo_name:
        print("ERROR: pass --meta or --repo <name>", file=sys.stderr)
        return 1

    cdir = config_dir or (Path(".").resolve() / "config")

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

    if meta:
        entry = sca.meta
        if entry is None:
            print("ERROR: scaffold-<org>.yaml has no 'meta' block", file=sys.stderr)
            return 1
        label = "meta"
        output_dir = workspace
    else:
        if repo_name not in sca.repos:
            print(f"ERROR: repo '{repo_name}' not in scaffold-<org>.yaml repos", file=sys.stderr)
            print(f"  Known repos: {sorted(sca.repos)}", file=sys.stderr)
            return 1
        entry = sca.repos[repo_name]
        label = repo_name
        output_dir = workspace

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

    try:
        _run_cookiecutter(template_url, ref, context, output_dir=output_dir, force=force)
    except Exception as exc:
        print(f"ERROR: cookiecutter failed: {exc}", file=sys.stderr)
        return 1

    print(f"  ✔  scaffold applied → {output_dir / (repo_name or sca.org + '-meta')}")
    print()

    # Determine next step
    target_flag = "--meta" if meta else f"--repo {repo_name}"
    if meta:
        next_cmd = f"launchpad apply-harness --meta --apply"
    else:
        next_cmd = f"launchpad apply-harness --repo {repo_name} --apply"

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  NEXT:                                                       ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  {next_cmd:<60}  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    return 0
