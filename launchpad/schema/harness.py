"""HarnessConfig schema — governance envelope per stack profile.

File: config/harness-<org>.yaml
Kind: HarnessConfig

A harness = a pinned constitution (rules submodule) + optional agent skills.
Profiles map stack names to harness resources.

Fields
------
org             Must match programme.yaml org.
profiles        Map of stack name → HarnessProfile.
  constitution
    repo        GitHub repo slug for rules (e.g. "python-services-rules").
    org         Optional override org; defaults to drivestream-lab.
    ref         Git ref (branch or tag, e.g. "v1.2.0").
  skills        List of agent skill repos (optional).
    repo        Skill repo slug.
    org         Optional override org.
    ref         Git ref.
repos           Map of repo slug → harness_profile (stack override per-repo).
                If absent, harness_profile defaults to repo.stack from governance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from launchpad.schema.errors import SchemaError

API_VERSION = "launchpad/v1"
KIND = "HarnessConfig"

_PLATFORM_ORG = "drivestream-lab"


class ConstitutionRef:
    def __init__(self, raw: dict[str, Any], *, profile: str, path: str = "") -> None:
        repo = str(raw.get("repo") or "").strip()
        if not repo:
            raise SchemaError(
                f"profiles.{profile!r}.constitution missing required field 'repo'",
                path=path,
            )
        self.repo = repo
        self.org = str(raw.get("org") or _PLATFORM_ORG).strip()
        ref = str(raw.get("ref") or "").strip()
        if not ref:
            raise SchemaError(
                f"profiles.{profile!r}.constitution missing required field 'ref'",
                path=path,
                hint="Pin to a tag or branch, e.g. ref: v1.2.0",
            )
        self.ref = ref

    @property
    def submodule_url(self) -> str:
        return f"https://github.com/{self.org}/{self.repo}"


class SkillRef:
    def __init__(self, raw: dict[str, Any], *, profile: str, idx: int, path: str = "") -> None:
        repo = str(raw.get("repo") or "").strip()
        if not repo:
            raise SchemaError(
                f"profiles.{profile!r}.skills[{idx}] missing required field 'repo'",
                path=path,
            )
        self.repo = repo
        self.org = str(raw.get("org") or _PLATFORM_ORG).strip()
        self.ref = str(raw.get("ref") or "").strip()


class HarnessProfile:
    def __init__(self, name: str, raw: dict[str, Any], *, path: str = "") -> None:
        self.name = name
        constitution_raw = raw.get("constitution") or {}
        if not isinstance(constitution_raw, dict):
            raise SchemaError(
                f"profiles.{name!r}.constitution must be a mapping", path=path
            )
        self.constitution = ConstitutionRef(constitution_raw, profile=name, path=path)
        skills_raw = raw.get("skills") or []
        if not isinstance(skills_raw, list):
            raise SchemaError(f"profiles.{name!r}.skills must be a list", path=path)
        self.skills: list[SkillRef] = [
            SkillRef(s, profile=name, idx=i, path=path) for i, s in enumerate(skills_raw)
        ]


class HarnessSchema:
    """Validated, normalised representation of harness-<org>.yaml."""

    def __init__(self, raw: dict[str, Any], *, path: str = "") -> None:
        self._path = path
        self.org: str = ""
        self.profiles: dict[str, HarnessProfile] = {}
        self.repos: dict[str, str] = {}
        self._validate(raw)

    def _validate(self, raw: dict[str, Any]) -> None:
        p = self._path

        org = str(raw.get("org") or "").strip()
        if not org:
            raise SchemaError(
                "harness YAML missing required field 'org'",
                path=p,
                hint="Set org: to match your programme.yaml org",
            )
        self.org = org

        profiles_raw = raw.get("profiles") or {}
        if not isinstance(profiles_raw, dict):
            raise SchemaError("'profiles' must be a mapping", path=p)
        for pname, pdata in profiles_raw.items():
            if not isinstance(pdata, dict):
                raise SchemaError(f"profiles.{pname!r} must be a mapping", path=p)
            self.profiles[pname] = HarnessProfile(pname, pdata, path=p)

        repos_raw = raw.get("repos") or {}
        if not isinstance(repos_raw, dict):
            raise SchemaError("'repos' must be a mapping", path=p)
        for repo_name, harness_profile in repos_raw.items():
            if harness_profile and harness_profile not in self.profiles:
                raise SchemaError(
                    f"repos.{repo_name!r} references unknown profile {harness_profile!r}",
                    path=p,
                    hint=f"Add profile {harness_profile!r} to profiles: or use one of: {sorted(self.profiles)}",
                )
            self.repos[repo_name] = str(harness_profile or "")

    def resolve_profile(self, repo_name: str, stack: str) -> str | None:
        """Return the harness profile for a repo, defaulting to its stack."""
        if repo_name in self.repos:
            return self.repos[repo_name] or stack
        return stack if stack in self.profiles else None


def load_harness(path: str | Path) -> HarnessSchema:
    """Load and validate a harness-<org>.yaml from *path*."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise SchemaError(f"Harness YAML not found: {p}")
    with p.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise SchemaError(f"Harness YAML must be a YAML mapping: {p}")
    return HarnessSchema(raw, path=str(p))
