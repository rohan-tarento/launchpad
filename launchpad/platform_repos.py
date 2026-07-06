"""Public OSS repositories hosted under drivestream-lab.

Tenant forge org (``OnboardingSpec.org``) is where private app repos and
``<client>-meta`` live. Platform constitution, skills, and cookiecutter
foundations always resolve here — independent of the tenant forge org.
"""

from __future__ import annotations

PLATFORM_ORG = "drivestream-lab"

PRAYOG_SKILLS_REPO = f"{PLATFORM_ORG}/prayog-skills"

RULES_REPO_SLUGS: dict[str, str] = {
    "python": "python-services-rules",
    "frontend": "nextjs-bff-rules",
    "data_platform": "data-platform-rules",
}

FOUNDATION_REPO_SLUGS: dict[str, str] = {
    "python-backend": "python-fastapi-foundation",
    "tenant-meta": "tenant-meta-foundation",
    "frontend": "nextjs-bff-foundation",
}

DEFAULT_AGENT_SKILLS_REF = "v0.4.0"
DEFAULT_RULES_REF = "v0.1.0"


def platform_repo(slug: str) -> str:
    """Return ``drivestream-lab/<slug>``."""
    return f"{PLATFORM_ORG}/{slug}"


def platform_rules_repo(profile_key: str) -> str:
    """Harness rules submodule repo for a profile key (python, frontend, data_platform)."""
    try:
        slug = RULES_REPO_SLUGS[profile_key]
    except KeyError as exc:
        raise KeyError(f"unknown rules profile key: {profile_key!r}") from exc
    return platform_repo(slug)


def gh_cookiecutter_template(profile_name: str) -> str:
    """Cookiecutter ``gh:`` URL for a scaffold profile."""
    try:
        slug = FOUNDATION_REPO_SLUGS[profile_name]
    except KeyError as exc:
        raise KeyError(f"unknown foundation profile: {profile_name!r}") from exc
    return f"gh:{platform_repo(slug)}"
