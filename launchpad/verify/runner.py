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
) -> bool:
    org = ctx.get("org", "")
    all_ok = True
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
            all_ok = _check(check_id, False, "unknown check id") and False
            continue
        try:
            ok, detail = handler(client, org, ctx, spec)
            if not _check(check_id, ok, detail):
                all_ok = False
        except Exception as exc:
            if not _check(check_id, False, str(exc)):
                all_ok = False
    return all_ok


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
        if not _run_checks(client, ctx, phase="scopes"):
            _fail_scopes()
        print("")
        if phase == "scopes":
            print("=== verify-platform: OK (scopes) ===")
            return

    if phase in (None, "applied"):
        print("Platform state:")
        if not _run_checks(client, ctx, phase="applied"):
            raise VerifyError("platform verify failed — run setup-platform --apply")
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
