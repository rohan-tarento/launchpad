"""Resolve prayog-skills bundles from profile YAML or meta-pm tree convention."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


class PrayogProfileError(RuntimeError):
    pass


_META_PM_PROFILE = "meta-pm"
_SKILL_NAME_RE = re.compile(r"^---\s*\n(?:.*\n)*?name:\s*(\S+)", re.MULTILINE)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PrayogProfileError(f"invalid YAML mapping in {path}")
    return data


def read_skill_name(skill_md: Path) -> str | None:
    """Parse skill name from SKILL.md frontmatter, if present."""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    match = _SKILL_NAME_RE.match(text)
    return match.group(1) if match else None


def discover_skill_paths(prayog_root: Path) -> dict[str, str]:
    """Map skill name → repo-relative path for every skills/**/SKILL.md."""
    out: dict[str, str] = {}
    skills_root = prayog_root / "skills"
    if not skills_root.is_dir():
        return out
    for skill_md in sorted(skills_root.glob("**/SKILL.md")):
        rel = skill_md.relative_to(prayog_root).as_posix()
        name = read_skill_name(skill_md) or skill_md.parent.name
        out[name] = rel
    return out


def meta_pm_skill_names_from_tree(prayog_root: Path) -> list[str]:
    """meta-pm @ prayog v0.3.0: all skills/requirements/* + generate-work-manifest."""
    names: list[str] = []
    requirements = prayog_root / "skills" / "requirements"
    if requirements.is_dir():
        for child in sorted(requirements.iterdir()):
            if child.is_dir() and (child / "SKILL.md").is_file():
                names.append(child.name)
    manifest = prayog_root / "skills" / "backlog" / "generate-work-manifest" / "SKILL.md"
    if manifest.is_file() and "generate-work-manifest" not in names:
        names.append("generate-work-manifest")
    return names


def skill_names_from_profile_yaml(data: dict[str, Any], profile_name: str) -> list[str]:
    """Extract ordered skill names from a prayog profiles/*.yaml file."""
    if "development_skills" in data:
        skills = data["development_skills"]
        if isinstance(skills, list):
            return [str(s) for s in skills]

    reqs = data.get("requirements_skills")
    backlog = data.get("backlog_skills")
    if isinstance(reqs, list) or isinstance(backlog, list):
        out: list[str] = []
        if isinstance(reqs, list):
            out.extend(str(s) for s in reqs)
        if isinstance(backlog, list):
            out.extend(str(s) for s in backlog)
        return out

    pm = data.get("pm_skills")
    if isinstance(pm, list):
        return [str(s) for s in pm]

    if profile_name == _META_PM_PROFILE:
        return []

    raise PrayogProfileError(f"profile {profile_name!r} has no recognized skill list keys")


def skill_names_for_profile(prayog_root: Path, profile_name: str) -> list[str]:
    """Resolve skill names from prayog SSOT for a harness profile."""
    profile_file = prayog_root / "profiles" / f"{profile_name}.yaml"
    if profile_file.is_file():
        names = skill_names_from_profile_yaml(_load_yaml(profile_file), profile_name)
        if names:
            return names

    if profile_name == _META_PM_PROFILE:
        names = meta_pm_skill_names_from_tree(prayog_root)
        if names:
            return names

    raise PrayogProfileError(
        f"no skills resolved for prayog profile {profile_name!r} under {prayog_root}"
    )


def resolve_agent_skills(
    agent_skills: dict[str, Any],
    *,
    harness_profile_name: str,
    prayog_root: Path,
) -> dict[str, Any]:
    """Return agent_skills with skills + skill_paths resolved from prayog @ ref."""
    ref = str(agent_skills.get("ref", ""))
    if not ref:
        raise PrayogProfileError("agent_skills requires ref")

    profile_name = str(agent_skills.get("profile") or harness_profile_name)
    explicit = agent_skills.get("skills")
    if explicit:
        skill_names = [str(s) for s in explicit]
    else:
        skill_names = skill_names_for_profile(prayog_root, profile_name)

    if not skill_names:
        raise PrayogProfileError(f"no skills resolved for profile {profile_name!r}")

    all_paths = discover_skill_paths(prayog_root)
    paths_map: dict[str, str] = {}
    missing: list[str] = []
    for name in skill_names:
        path = all_paths.get(name)
        if path:
            paths_map[name] = path
        else:
            missing.append(name)
    if missing:
        raise PrayogProfileError(
            f"skills missing from prayog tree @ {ref}: {', '.join(missing)}"
        )

    merged = dict(agent_skills)
    merged["profile"] = profile_name
    merged["skills"] = skill_names
    merged["skill_paths"] = paths_map
    return merged
