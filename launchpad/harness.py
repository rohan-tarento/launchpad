"""Sync and verify harness pins (rules submodule + prayog-skills bundle) in app repos."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from launchpad.config import load_harness_config, tenant_root
from launchpad.paths import resolve_template


class HarnessError(RuntimeError):
    pass

_SKILLS_CLI = ["npx", "skills@1.5.11"]
_LEGACY_SKILLS_DEFAULT = ".cursor/skills"


def _run_git(args: list[str], *, cwd: Path, dry_run: bool) -> subprocess.CompletedProcess[str] | None:
    cmd = ["git", *args]
    if dry_run:
        print(f"  [dry-run] {' '.join(cmd)}  (cwd={cwd})")
        return None
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_cmd(cmd: list[str], *, cwd: Path, dry_run: bool) -> None:
    print(f"  [cmd] {' '.join(cmd)}  (cwd={cwd})")
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, check=True)


def _is_submodule(repo: Path, rel_path: str) -> bool:
    gitmodules = repo / ".gitmodules"
    if not gitmodules.is_file():
        return False
    text = gitmodules.read_text(encoding="utf-8")
    return f'path = {rel_path}' in text or f"path = {rel_path}" in text


def _submodule_head(repo: Path, rel_path: str) -> str | None:
    sub = repo / rel_path
    if not (sub / ".git").exists():
        return None
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=sub,
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _tag_commit(repo: Path, rel_path: str, tag: str) -> str | None:
    """Resolve tag to commit SHA (handles annotated tags via ^{commit})."""
    sub = repo / rel_path
    if not (sub / ".git").exists():
        return None
    for ref in (tag, f"refs/tags/{tag}"):
        for suffix in ("^{commit}", ""):
            try:
                proc = subprocess.run(
                    ["git", "rev-parse", f"{ref}{suffix}"],
                    cwd=sub,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return proc.stdout.strip()
            except subprocess.CalledProcessError:
                continue
    return None


def _render(text: str, values: dict[str, str]) -> str:
    out = text
    for key, val in values.items():
        out = out.replace(f"{{{{{key}}}}}", val)
    return out


def _resolve_workspace(cfg: dict[str, Any], workspace: Path | None) -> Path:
    root = tenant_root()
    if workspace is not None:
        return workspace.resolve()
    default = str(cfg.get("default_workspace", ".."))
    return (root / default).resolve()


def _repo_entry(cfg: dict[str, Any], repo_name: str) -> dict[str, Any]:
    repos = cfg.get("repos") or {}
    if repo_name not in repos:
        known = ", ".join(sorted(repos.keys()))
        raise HarnessError(f"repo {repo_name!r} not in harness config (known: {known})")
    meta = repos[repo_name]
    if not isinstance(meta, dict):
        raise HarnessError(f"invalid repo entry for {repo_name!r}")
    profile_name = str(meta.get("profile", ""))
    profiles = cfg.get("profiles") or {}
    if profile_name not in profiles:
        raise HarnessError(f"profile {profile_name!r} missing for repo {repo_name!r}")
    profile = profiles[profile_name]
    if not isinstance(profile, dict):
        raise HarnessError(f"invalid profile {profile_name!r}")
    return {
        "name": repo_name,
        "profile_name": profile_name,
        "profile": profile,
        "service_name": str(meta.get("service_name", repo_name)),
        "conda_env": str(meta.get("conda_env", repo_name)),
        "verify_smoke": str(meta.get("verify_smoke", "make test")),
    }


def _agent_skills_spec(profile: dict[str, Any]) -> dict[str, Any]:
    spec = profile.get("agent_skills") or {}
    if not spec:
        raise HarnessError("profile missing agent_skills block")
    ref = str(spec.get("ref", ""))
    skills = spec.get("skills") or []
    if not ref or not skills:
        raise HarnessError("agent_skills requires ref and skills list")
    return spec


def _skills_list_yaml(skills: list[str]) -> str:
    return "\n".join(f"    - {s}" for s in skills)


def _write_pin(
    repo_path: Path,
    pin_template: Path,
    values: dict[str, str],
    *,
    dry_run: bool,
) -> None:
    dest = repo_path / ".harness-pin.yaml"
    content = _render(pin_template.read_text(encoding="utf-8"), values)
    print(f"[pin] {dest}")
    if dry_run:
        print(content.rstrip())
        return
    dest.write_text(content, encoding="utf-8")


def _write_agents(repo_path: Path, agents_template: Path, values: dict[str, str], *, dry_run: bool) -> None:
    dest = repo_path / "AGENTS.md"
    content = _render(agents_template.read_text(encoding="utf-8"), values)
    print(f"[agents] {dest}")
    if dry_run:
        return
    dest.write_text(content, encoding="utf-8")


def _ensure_submodule(
    repo_path: Path,
    *,
    rel_path: str,
    url: str,
    ref: str,
    dry_run: bool,
) -> None:
    dest = repo_path / rel_path
    print(f"[submodule] {rel_path} → {url} @ {ref}")

    if _is_submodule(repo_path, rel_path):
        _run_git(["submodule", "update", "--init", rel_path], cwd=repo_path, dry_run=dry_run)
        if not dry_run:
            _run_git(["fetch", "--tags", "origin"], cwd=dest, dry_run=False)
            _run_git(["checkout", ref], cwd=dest, dry_run=False)
        else:
            _run_git(["fetch", "--tags", "origin"], cwd=dest, dry_run=True)
            _run_git(["checkout", ref], cwd=dest, dry_run=True)
        return

    if dest.exists():
        print(f"  convert {rel_path}: remove copied tree, add submodule")
        if dry_run:
            _run_git(["rm", "-rf", rel_path], cwd=repo_path, dry_run=True)
            _run_git(["submodule", "add", url, rel_path], cwd=repo_path, dry_run=True)
            _run_git(["checkout", ref], cwd=dest, dry_run=True)
            return
        if dest.is_dir():
            shutil.rmtree(dest)
        _run_git(["rm", "-rf", "--ignore-unmatch", rel_path], cwd=repo_path, dry_run=False)
        _run_git(["submodule", "add", url, rel_path], cwd=repo_path, dry_run=False)
        _run_git(["fetch", "--tags", "origin"], cwd=dest, dry_run=False)
        _run_git(["checkout", ref], cwd=dest, dry_run=False)
        return

    if dry_run:
        _run_git(["submodule", "add", url, rel_path], cwd=repo_path, dry_run=True)
        _run_git(["checkout", ref], cwd=dest, dry_run=True)
        return

    _run_git(["submodule", "add", url, rel_path], cwd=repo_path, dry_run=False)
    _run_git(["fetch", "--tags", "origin"], cwd=dest, dry_run=False)
    _run_git(["checkout", ref], cwd=dest, dry_run=False)


def _remove_legacy_skills_submodule(
    repo_path: Path,
    legacy_path: str,
    *,
    dry_run: bool,
) -> None:
    if not legacy_path or not _is_submodule(repo_path, legacy_path):
        return
    print(f"[migrate] remove legacy skills submodule {legacy_path}")
    _run_git(["submodule", "deinit", "-f", legacy_path], cwd=repo_path, dry_run=dry_run)
    _run_git(["rm", "-f", legacy_path], cwd=repo_path, dry_run=dry_run)


def _resolve_prayog_source(ws: Path, agent_skills: dict[str, Any]) -> Path | None:
    """Prefer local lab clone when present (dev); None → clone from url."""
    local = agent_skills.get("local_path")
    if local:
        candidate = (ws / str(local)).resolve()
        if candidate.is_dir():
            return candidate
    skills = (ws.parent / "prayog-skills").resolve()
    if skills.is_dir():
        return skills
    return None


def _materialize_prayog_source(
    ws: Path,
    agent_skills: dict[str, Any],
    *,
    dry_run: bool,
) -> Path:
    local = _resolve_prayog_source(ws, agent_skills)
    if local is not None:
        print(f"[agent_skills] using local source {local}")
        return local

    url = str(agent_skills.get("url", ""))
    ref = str(agent_skills.get("ref", "main"))
    if not url:
        raise HarnessError("agent_skills.url required when local prayog-skills not found")

    tmp = Path(tempfile.mkdtemp(prefix="prayog-skills-"))
    print(f"[agent_skills] clone {url} @ {ref} → {tmp}")
    if dry_run:
        return tmp
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", ref, url, str(tmp)],
        check=True,
    )
    return tmp


def _remove_obsolete_harness_dir(repo_path: Path, *, dry_run: bool) -> None:
    """Drop legacy .harness/ — layout SSOT is prayog-skills layout-defaults + pin profile name."""
    obsolete = repo_path / ".harness"
    if not obsolete.is_dir():
        return
    print(f"[migrate] remove obsolete {obsolete}")
    if not dry_run:
        shutil.rmtree(obsolete)


def _ensure_gitignore_entries(repo_path: Path, *, dry_run: bool) -> None:
    """Ignore installed skill copies; skills-lock.json is committed."""
    lines_to_add = [".agents/"]
    path = repo_path / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    missing = [line for line in lines_to_add if line not in existing]
    if not missing:
        return
    print(f"[gitignore] append {missing}")
    if dry_run:
        return
    suffix = "" if existing.endswith("\n") or not existing else "\n"
    path.write_text(existing + suffix + "\n".join(missing) + "\n", encoding="utf-8")


def _prune_agent_skills(
    repo_path: Path,
    install_rel: str,
    allowed: set[str],
    *,
    dry_run: bool,
) -> None:
    base = repo_path / install_rel
    if not base.is_dir():
        return
    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name in allowed:
            continue
        print(f"[agent_skills] prune {child.name}")
        _run_cmd([*_SKILLS_CLI, "remove", child.name, "-y"], cwd=repo_path, dry_run=dry_run)


def _normalize_skills_lock(
    repo_path: Path,
    agent_skills: dict[str, Any],
    *,
    dry_run: bool,
) -> None:
    """Keep only the harness bundle in skills-lock.json with canonical github source."""
    lock_name = str(agent_skills.get("lock_file", "skills-lock.json"))
    path = repo_path / lock_name
    allowed = [str(s) for s in (agent_skills.get("skills") or [])]
    paths_map = agent_skills.get("skill_paths") or {}
    repo_slug = str(agent_skills.get("repo", "drivestream-lab/prayog-skills"))
    print(f"[agent_skills] normalize {lock_name} → {allowed}")
    if dry_run:
        return
    prior = _read_skills_lock(repo_path, lock_name)
    prior_skills = prior.get("skills") if isinstance(prior.get("skills"), dict) else {}
    out_skills: dict[str, Any] = {}
    for name in allowed:
        entry: dict[str, Any] = {
            "source": repo_slug,
            "sourceType": "github",
        }
        rel = paths_map.get(name)
        if rel:
            entry["skillPath"] = str(rel)
        if name in prior_skills and prior_skills[name].get("computedHash"):
            entry["computedHash"] = prior_skills[name]["computedHash"]
        out_skills[name] = entry
    payload = {"version": prior.get("version", 1), "skills": out_skills}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _install_agent_skills(
    repo_path: Path,
    source_root: Path,
    agent_skills: dict[str, Any],
    *,
    dry_run: bool,
) -> None:
    skills = [str(s) for s in (agent_skills.get("skills") or [])]
    install_rel = str(agent_skills.get("install_path", ".agents/skills"))
    _prune_agent_skills(repo_path, install_rel, set(skills), dry_run=dry_run)
    cmd = [*_SKILLS_CLI, "add", str(source_root), "-a", "cursor", "-y"]
    for name in skills:
        cmd.extend(["-s", name])
    print(f"[agent_skills] install {skills}")
    _run_cmd(cmd, cwd=repo_path, dry_run=dry_run)
    _normalize_skills_lock(repo_path, agent_skills, dry_run=dry_run)


def sync_harness(
    *,
    config_path: Path | str,
    repo_name: str,
    workspace: Path | None = None,
    dry_run: bool = True,
    skip_agents: bool = False,
) -> None:
    root = tenant_root()
    cfg = load_harness_config(config_path)
    entry = _repo_entry(cfg, repo_name)
    profile = entry["profile"]
    ws = _resolve_workspace(cfg, workspace)
    repo_path = ws / repo_name

    if not (repo_path / ".git").is_dir():
        raise HarnessError(f"no git repo at {repo_path} (use --workspace)")

    rules = profile.get("rules") or {}
    agent_skills = _agent_skills_spec(profile)
    rules_ref = str(rules.get("ref", ""))
    agent_ref = str(agent_skills.get("ref", ""))
    if not rules_ref:
        raise HarnessError(f"profile {entry['profile_name']!r} missing rules ref")

    print(f"[harness] sync {repo_name} profile={entry['profile_name']} dry_run={dry_run}")

    pin_tpl_name = str(profile.get("pin_template", "templates/harness-pin.yaml"))
    agents_tpl_name = str(profile.get("agents_template", "templates/AGENTS.python.md"))
    try:
        pin_tpl = resolve_template(pin_tpl_name)
        agents_tpl = resolve_template(agents_tpl_name)
    except FileNotFoundError as exc:
        raise HarnessError(str(exc)) from exc

    skill_names = [str(s) for s in (agent_skills.get("skills") or [])]
    values = {
        "REPO": repo_name,
        "RULES_REF": rules_ref,
        "RULES_PIN": rules_ref,
        "AGENT_SKILLS_REF": agent_ref,
        "AGENT_SKILLS_LIST": _skills_list_yaml(skill_names),
        "SERVICE_NAME": entry["service_name"],
        "CONDA_ENV": entry["conda_env"],
        "VERIFY_SMOKE": entry["verify_smoke"],
    }

    _write_pin(repo_path, pin_tpl, values, dry_run=dry_run)
    if not skip_agents:
        _write_agents(repo_path, agents_tpl, values, dry_run=dry_run)

    _ensure_submodule(
        repo_path,
        rel_path=str(rules.get("path", ".cursor/rules")),
        url=str(rules.get("url", "")),
        ref=rules_ref,
        dry_run=dry_run,
    )

    legacy = str(profile.get("legacy_skills_submodule_path", _LEGACY_SKILLS_DEFAULT))
    _remove_legacy_skills_submodule(repo_path, legacy, dry_run=dry_run)

    prayog_source = _materialize_prayog_source(ws, agent_skills, dry_run=dry_run)
    try:
        _remove_obsolete_harness_dir(repo_path, dry_run=dry_run)
        _ensure_gitignore_entries(repo_path, dry_run=dry_run)
        _install_agent_skills(repo_path, prayog_source, agent_skills, dry_run=dry_run)
    finally:
        if prayog_source.name.startswith("prayog-skills-") and not dry_run:
            shutil.rmtree(prayog_source, ignore_errors=True)

    if dry_run:
        print(f"[done] dry-run — re-run with --apply to write {repo_path}")
    else:
        print(f"[done] synced harness at {repo_path}")
        print("  → local: .agents/skills/ ready for Cursor slash commands")
        print("  → optional git PR (chore/sync-harness-pins): .harness-pin.yaml, AGENTS.md,")
        print("    skills-lock.json — skip when INIT/spec PR only")


def _read_skills_lock(repo_path: Path, lock_name: str) -> dict[str, Any]:
    path = repo_path / lock_name
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def verify_harness(
    *,
    config_path: Path | str,
    repo_name: str = "",
    workspace: Path | None = None,
) -> list[str]:
    """Return list of error messages (empty = pass)."""
    cfg = load_harness_config(config_path)
    ws = _resolve_workspace(cfg, workspace)
    repos_cfg = cfg.get("repos") or {}
    targets = [repo_name] if repo_name else sorted(repos_cfg.keys())
    errors: list[str] = []

    for name in targets:
        if name not in repos_cfg:
            errors.append(f"{name}: not in harness config")
            continue
        try:
            entry = _repo_entry(cfg, name)
        except HarnessError as exc:
            errors.append(f"{name}: {exc}")
            continue

        profile = entry["profile"]
        repo_path = ws / name
        prefix = f"{name}:"

        if not (repo_path / ".git").is_dir():
            errors.append(f"{prefix} no clone at {repo_path}")
            continue

        try:
            agent_skills = _agent_skills_spec(profile)
        except HarnessError as exc:
            errors.append(f"{prefix} {exc}")
            continue

        agent_ref = str(agent_skills.get("ref", ""))
        skill_names = [str(s) for s in (agent_skills.get("skills") or [])]
        lock_name = str(agent_skills.get("lock_file", "skills-lock.json"))
        install_rel = str(agent_skills.get("install_path", ".agents/skills"))
        pin_path = repo_path / ".harness-pin.yaml"
        if not pin_path.is_file():
            errors.append(f"{prefix} missing .harness-pin.yaml")
        else:
            pin_text = pin_path.read_text(encoding="utf-8")
            rules_ref = str((profile.get("rules") or {}).get("ref", ""))
            if rules_ref and f"ref: {rules_ref}" not in pin_text:
                errors.append(f"{prefix} .harness-pin.yaml rules ref != {rules_ref}")
            if agent_ref and f"ref: {agent_ref}" not in pin_text:
                errors.append(f"{prefix} .harness-pin.yaml agent_skills ref != {agent_ref}")
            for sk in skill_names:
                if sk not in pin_text:
                    errors.append(f"{prefix} .harness-pin.yaml missing skill {sk!r}")

        rules_spec = profile.get("rules") or {}
        rules_rel = str(rules_spec.get("path", ".cursor/rules"))
        rules_ref = str(rules_spec.get("ref", ""))
        if not rules_rel:
            errors.append(f"{prefix} profile missing rules path")
        elif not _is_submodule(repo_path, rules_rel):
            errors.append(f"{prefix} {rules_rel} is not a git submodule")
        else:
            head = _submodule_head(repo_path, rules_rel)
            tag_sha = _tag_commit(repo_path, rules_rel, rules_ref)
            if not head:
                errors.append(f"{prefix} {rules_rel} submodule not initialized")
            elif not tag_sha:
                errors.append(f"{prefix} {rules_rel} tag {rules_ref!r} not found in submodule")
            elif head != tag_sha:
                errors.append(f"{prefix} {rules_rel} HEAD {head[:7]} != {rules_ref} ({tag_sha[:7]})")

        legacy = str(profile.get("legacy_skills_submodule_path", _LEGACY_SKILLS_DEFAULT))
        if legacy and _is_submodule(repo_path, legacy):
            errors.append(
                f"{prefix} legacy skills submodule {legacy} still present — run sync-harness --apply"
            )

        lock = _read_skills_lock(repo_path, lock_name)
        locked = lock.get("skills") if isinstance(lock.get("skills"), dict) else {}
        if not locked:
            errors.append(f"{prefix} missing or empty {lock_name}")
        else:
            for sk in skill_names:
                if sk not in locked:
                    errors.append(f"{prefix} {lock_name} missing skill {sk!r}")
                skill_md = repo_path / install_rel / sk / "SKILL.md"
                if not skill_md.is_file():
                    errors.append(f"{prefix} missing installed skill {install_rel}/{sk}/SKILL.md")

        agents_path = repo_path / "AGENTS.md"
        if agents_path.is_file():
            agents = agents_path.read_text(encoding="utf-8")
            if rules_ref and rules_ref not in agents:
                errors.append(f"{prefix} AGENTS.md missing rules pin {rules_ref}")
            if agent_ref and agent_ref not in agents:
                errors.append(f"{prefix} AGENTS.md missing agent_skills ref {agent_ref}")
            for cmd in ("/pre-implement", "/verify"):
                if cmd not in agents:
                    errors.append(f"{prefix} AGENTS.md missing {cmd}")
            if "python-services-skills" in agents:
                errors.append(f"{prefix} AGENTS.md still references deprecated python-services-skills")
            if "testing-and-verification.md" in agents:
                errors.append(f"{prefix} AGENTS.md still references testing-and-verification.md (Option B)")
            if re.search(r"QUALITY-[A-Z]+-\d+", agents):
                errors.append(f"{prefix} AGENTS.md contains QUALITY-* initiative block (use board Spec path)")
        else:
            errors.append(f"{prefix} missing AGENTS.md")

        for forbidden in profile.get("forbidden_paths") or []:
            fpath = repo_path / str(forbidden)
            if fpath.exists():
                errors.append(f"{prefix} forbidden path exists: {forbidden}")

    return errors


def run_sync(
    *,
    config_path: Path | str,
    repo_name: str,
    workspace: Path | None = None,
    dry_run: bool = True,
    skip_agents: bool = False,
) -> None:
    sync_harness(
        config_path=config_path,
        repo_name=repo_name,
        workspace=workspace,
        dry_run=dry_run,
        skip_agents=skip_agents,
    )


def run_verify(
    *,
    config_path: Path | str,
    repo_name: str = "",
    workspace: Path | None = None,
) -> None:
    errors = verify_harness(config_path=config_path, repo_name=repo_name, workspace=workspace)
    if not errors:
        scope = repo_name or "all repos"
        print(f"[ok] harness verify passed ({scope})")
        return
    for msg in errors:
        print(f"FAIL: {msg}")
    raise HarnessError(f"harness verify failed ({len(errors)} issue(s))")
