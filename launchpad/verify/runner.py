"""Run VerifyManifest checks from YAML."""

from __future__ import annotations

from launchpad.config import load_verify_manifest, resolve_config_path
from launchpad.github_client import GitHubClient
from launchpad.verify import checks


class VerifyError(RuntimeError):
    """One or more required platform checks failed."""


def _check(label: str, ok: bool, detail: str = "") -> bool:
    mark = "ok" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{mark}] {label}{suffix}")
    return ok


def _when_ok(when: str, ctx: dict) -> bool:
    if not when:
        return True
    if when == "project.issue_types_required":
        project = ctx.get("project") or {}
        return bool(project.get("issue_types_required"))
    return True


def _run_checks(
    client: GitHubClient,
    ctx: dict,
    *,
    phase: str | None = None,
) -> tuple[bool, list[str]]:
    org = ctx.get("org", "")
    all_ok = True
    failed: list[str] = []
    handlers = checks.CHECKS

    for spec in ctx.get("checks") or []:
        check_id = spec.get("id", "")
        check_phase = spec.get("phase", "applied")
        if phase and check_phase != phase:
            continue
        if not spec.get("required", True):
            continue
        if not _when_ok(str(spec.get("when", "")), ctx):
            continue
        handler = handlers.get(check_id)
        if not handler:
            if not _check(check_id, False, "unknown check id"):
                all_ok = False
                failed.append(check_id)
            continue
        try:
            ok, detail = handler(client, org, ctx, spec)
            if not _check(check_id, ok, detail):
                all_ok = False
                failed.append(check_id)
        except Exception as exc:
            if not _check(check_id, False, str(exc)):
                all_ok = False
                failed.append(check_id)
    return all_ok, failed


def run(
    client: GitHubClient,
    *,
    config_path: str | None = None,
    org: str = "",
    phase: str | None = None,
) -> None:
    """Run verify manifest. phase: scopes | applied | None (all)."""
    cfg_path = resolve_config_path("verify-platform", org=org, explicit=config_path)
    ctx = load_verify_manifest(cfg_path)
    org = org or ctx.get("org", "")

    title = "verify-platform"
    if phase == "scopes":
        title += " (scopes)"
    elif phase == "applied":
        title += " (applied)"

    print(f"=== {title} ===")
    print(f"Org: {org}")
    print(f"Config: {cfg_path}")
    print(f"Authenticated as: {client.whoami()}")
    print("")

    if phase in (None, "scopes"):
        print("Token / API:")
        scopes_ok, _ = _run_checks(client, ctx, phase="scopes")
        if not scopes_ok:
            _fail_scopes()
        print("")
        if phase == "scopes":
            print("=== verify-platform: OK (scopes) ===")
            return

    if phase in (None, "applied"):
        print("Platform state:")
        applied_ok, failed = _run_checks(client, ctx, phase="applied")
        if not applied_ok:
            _fail_applied(ctx, failed, org)
        print("")
        print("=== verify-platform: OK ===")


def run_applied(
    client: GitHubClient,
    *,
    config_path: str | None = None,
    org: str = "",
) -> None:
    """Applied checks only — gate for seed-work."""
    run(client, config_path=config_path, org=org, phase="applied")


def _fail_scopes() -> None:
    print("=== verify-platform: FAILED (scopes) ===")
    print("")
    print("Update PAT — playbook/python-automation.md § Create a PAT:")
    print("  Organization → Issue types: Read and write")
    print("  Organization → Projects: Read and write")
    print("  Organization → Administration: Read and write")
    raise VerifyError("factory PAT scopes insufficient")


def _fail_applied(ctx: dict, failed: list[str], org: str) -> None:
    print("")
    print("=== verify-platform: FAILED (applied) ===")
    if any(
        check_id in failed
        for check_id in ("gitflow.develop", "gitflow.default_branch", "repos.present")
    ):
        _print_repo_seed_hints(ctx, org)
    print("")
    print("Docs: docs/new-client.md · playbook/greenfield-app-repo.md")
    raise VerifyError("platform verify failed — see hints above")


def _print_repo_seed_hints(ctx: dict, org: str) -> None:
    gitflow = ctx.get("gitflow") or {}
    cfg_path = gitflow.get("path") or f"config/gitflow-{org}.yaml"
    options = gitflow.get("options") or {}
    print("")
    print("How to fix repo / branch checks:")
    print("  setup-platform seeds every gitflow repo (meta + apps): main → develop → default develop")
    if options.get("set_default_branch") is False:
        print("  options.set_default_branch: false — set develop as default branch via org owner in GitHub UI")
    else:
        print("  If seed-repos cannot PATCH default branch, set options.set_default_branch: false in gitflow YAML")
    print("")
    print("  Re-run:")
    print(f"    launchpad setup-platform --config config/platform-{org}.yaml --apply")
    print("  Or step-by-step:")
    print(f"    launchpad bootstrap-org --config config/org-{org}.yaml --apply")
    print(f"    launchpad seed-repos --config {cfg_path} --apply")
    print(f"    launchpad setup-gitflow --config {cfg_path} --apply")
    print(f"    launchpad verify-platform --config config/verify-platform-{org}.yaml")
