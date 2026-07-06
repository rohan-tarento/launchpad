"""Scaffold profile registry — extensible per stack (python-backend, frontend, …)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from launchpad.scaffold.errors import ScaffoldError
from launchpad.platform_repos import gh_cookiecutter_template, platform_repo


@dataclass(frozen=True)
class ScaffoldProfile:
    """One scaffold stack (cookiecutter today; other engines later)."""

    name: str
    engine: str
    template_env: str
    template_default: str
    cookiecutter_keys: frozenset[str]
    defaults: dict[str, str]
    implemented: bool = True
    aliases: tuple[str, ...] = ()

    def resolve_name(self) -> str:
        return self.name


_PROFILES: dict[str, ScaffoldProfile] = {}
_ALIASES: dict[str, str] = {}


def _register(profile: ScaffoldProfile) -> None:
    _PROFILES[profile.name] = profile
    for alias in profile.aliases:
        _ALIASES[alias] = profile.name


_PYTHON_BACKEND_DEFAULTS: dict[str, str] = {
    "auth_mode": "jwt",
    "has_postgres": "yes",
    "has_redis": "yes",
    "has_kafka": "no",
    "has_s3": "no",
    "has_cratedb": "no",
    "has_emqx": "no",
    "has_telemetry": "yes",
    "has_internal_api": "no",
    "default_port": "8000",
}

_PYTHON_BACKEND_KEYS = frozenset(
    {
        "service_name",
        "service_description",
        "default_port",
        "auth_mode",
        "has_postgres",
        "has_redis",
        "has_kafka",
        "has_s3",
        "has_cratedb",
        "has_emqx",
        "has_telemetry",
        "has_internal_api",
    }
)

_register(
    ScaffoldProfile(
        name="python-backend",
        engine="cookiecutter",
        template_env="LAUNCHPAD_PYTHON_FOUNDATION",
        template_default=gh_cookiecutter_template("python-backend"),
        cookiecutter_keys=_PYTHON_BACKEND_KEYS,
        defaults=_PYTHON_BACKEND_DEFAULTS,
    )
)

_register(
    ScaffoldProfile(
        name="frontend",
        engine="cookiecutter",
        template_env="LAUNCHPAD_NEXTJS_BFF_FOUNDATION",
        template_default=gh_cookiecutter_template("frontend"),
        cookiecutter_keys=frozenset(),
        defaults={},
        implemented=False,
        aliases=("nextjs-bff",),
    )
)

_TENANT_META_KEYS = frozenset(
    {
        "meta_repo",
        "client_id",
        "display_name",
        "org",
        "forge_type",
    }
)

_TENANT_META_DEFAULTS: dict[str, str] = {
    "client_id": "example",
    "display_name": "Example",
    "org": "example-org",
    "forge_type": "github",
}

_register(
    ScaffoldProfile(
        name="tenant-meta",
        engine="cookiecutter",
        template_env="LAUNCHPAD_META_FOUNDATION",
        template_default=f"gh:{platform_repo('tenant-meta-foundation')}",
        cookiecutter_keys=_TENANT_META_KEYS,
        defaults=_TENANT_META_DEFAULTS,
    )
)


def list_profiles(*, implemented_only: bool = False) -> list[str]:
    names = sorted(_PROFILES.keys())
    if implemented_only:
        return [n for n in names if _PROFILES[n].implemented]
    return names


def get_profile(name: str) -> ScaffoldProfile:
    key = _ALIASES.get(name, name)
    profile = _PROFILES.get(key)
    if profile is None:
        known = ", ".join(list_profiles())
        raise ScaffoldError(f"unknown scaffold profile {name!r} (known: {known})")
    return profile


def normalize_options(profile: ScaffoldProfile, raw: dict[str, Any]) -> dict[str, str]:
    """Validate and stringify cookiecutter extra_context keys."""
    if profile.engine != "cookiecutter":
        raise ScaffoldError(f"profile {profile.name!r} engine {profile.engine!r} is not supported yet")

    out: dict[str, str] = {}
    for key, value in raw.items():
        if key not in profile.cookiecutter_keys:
            allowed = ", ".join(sorted(profile.cookiecutter_keys))
            raise ScaffoldError(f"unknown option {key!r} for profile {profile.name!r} (allowed: {allowed})")
        out[key] = str(value)
    return out
