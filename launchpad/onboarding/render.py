"""Render tenant factory YAML and templates from OnboardingSpec."""

from __future__ import annotations

from typing import Any

import yaml

from launchpad.onboarding.context import OnboardingContext

_PRAYOG_SKILLS = [
    "spec-feasibility-review",
    "spec-implementation-plan",
    "pre-implement",
    "verify",
]

_SKILL_PATHS = {
    "spec-feasibility-review": "skills/development/spec-feasibility-review/SKILL.md",
    "spec-implementation-plan": "skills/development/spec-implementation-plan/SKILL.md",
    "pre-implement": "skills/development/pre-implement/SKILL.md",
    "verify": "skills/development/verify/SKILL.md",
}

_HARNESS_PROFILE_MAP = {
    "backend": "python-backend",
    "frontend": "frontend",
    "data_platform": "data-platform",
}

_GITFLOW_MERGE = {
    "backend": "backend",
    "frontend": "frontend",
    "platform": "platform",
    "data_platform": "data_platform",
}


def _dump(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


def _agent_skills_block(ctx: OnboardingContext) -> dict[str, Any]:
    ref = ctx.spec["agent_skills"]["ref"]
    repo = ctx.spec["agent_skills"]["repo"]
    host = "github.com" if ctx.forge_type == "github" else "gitlab.com"
    url = f"https://{host}/{repo}.git" if ctx.forge_type == "github" else f"{ctx.forge_host}/{repo}.git"
    return {
        "repo": repo,
        "url": url,
        "ref": ref,
        "skills": list(_PRAYOG_SKILLS),
        "skill_paths": dict(_SKILL_PATHS),
        "install_path": ".agents/skills",
        "lock_file": "skills-lock.json",
    }


def _rules_block(ctx: OnboardingContext, rules_key: str, default_repo_suffix: str) -> dict[str, Any]:
    rules = ctx.spec["rules"].get(rules_key) or {
        "repo": f"{ctx.org}/{default_repo_suffix}",
        "initial_ref": "v0.1.0",
    }
    repo = rules["repo"]
    ref = rules["initial_ref"]
    return {
        "repo": repo,
        "url": ctx.rules_git_url(repo),
        "ref": ref,
        "path": ".cursor/rules",
    }


def render_org_config(ctx: OnboardingContext) -> str:
    forge: dict[str, Any] = {"type": ctx.forge_type}
    if ctx.forge_type == "gitlab":
        forge["host"] = ctx.forge_host

    teams = []
    for team in ctx.spec["teams"]:
        entry: dict[str, Any] = {"slug": team["slug"]}
        if team["slug"] != "pm-team":
            entry["description"] = f"{team['slug']} — {ctx.display_name}"
            entry["privacy"] = "closed"
        else:
            entry["description"] = "Product / program managers"
            entry["privacy"] = "closed"
        teams.append(entry)

    data: dict[str, Any] = {
        "apiVersion": "launchpad/v1",
        "kind": "OrgConfig",
        "org": ctx.org,
        "forge": forge,
        "repos": [
            {
                "name": r["name"],
                "private": r["private"],
                "description": r["description"],
            }
            for r in ctx.spec["repos"]
        ],
        "labels": ctx.spec["labels"],
        "teams": teams,
    }
    return _dump(data)


def render_platform_config(ctx: OnboardingContext) -> str:
    org = ctx.org
    data = {
        "apiVersion": "launchpad/v1",
        "kind": "PlatformManifest",
        "org": org,
        "name": f"{ctx.display_name} platform baseline",
        "setup": [
            {"id": "repos", "command": "bootstrap-org", "config": f"config/org-{org}.yaml"},
            {"id": "teams", "command": "bootstrap-teams", "config": f"config/org-{org}.yaml"},
            {"id": "gitflow", "command": "setup-gitflow", "config": f"config/gitflow-{org}.yaml"},
            {"id": "board", "command": "bootstrap-project", "config": f"config/project-{org}.yaml"},
        ],
        "verify": {"config": f"config/verify-platform-{org}.yaml"},
    }
    return _dump(data)


def render_gitflow_config(ctx: OnboardingContext) -> str:
    org = ctx.org
    gf = ctx.spec["gitflow"]
    repos: dict[str, Any] = {
        ctx.meta_repo: {
            "profile": "platform",
            "develop_merge": "pm",
            "grant_read": ["backend", "frontend", "platform", "data_platform"],
        }
    }
    for repo in ctx.spec["repos"]:
        profile = repo["profile"]
        repos[repo["name"]] = {
            "profile": profile,
            "develop_merge": _GITFLOW_MERGE.get(profile, "backend"),
        }

    data = {
        "apiVersion": "launchpad/v1",
        "kind": "GitflowConfig",
        "org": org,
        "includes": {"org": f"config/org-{org}.yaml"},
        "options": {
            "require_ci": gf["require_ci"],
            "branch_naming": gf["branch_naming"],
            "with_templates": gf["with_templates"],
            "init_empty": False,
            "workspace": "..",
        },
        "branch_naming": {"mode": gf["branch_naming_mode"]},
        "teams": {
            "release_managers": ctx.team_slug("release_managers"),
            "pm": ctx.team_slug("pm"),
            "backend": ctx.team_slug("backend"),
            "frontend": ctx.team_slug("frontend"),
            "platform": ctx.team_slug("platform"),
            "data_platform": ctx.team_slug("data_platform"),
        },
        "profiles": {
            "backend": "backend",
            "frontend": "frontend",
            "platform": "platform",
            "data_platform": "data_platform",
        },
        "repos": repos,
    }
    return _dump(data)


def _harness_profile(
    ctx: OnboardingContext,
    profile_key: str,
    pin_template: str,
    agents_template: str,
    rules_key: str,
    default_suffix: str,
) -> dict[str, Any]:
    rules_spec = ctx.spec["rules"].get(rules_key) or {
        "repo": f"{ctx.org}/{default_suffix}",
        "initial_ref": "v0.1.0",
    }
    return {
        "rules": {
            "repo": rules_spec["repo"],
            "url": ctx.rules_git_url(rules_spec["repo"]),
            "ref": rules_spec["initial_ref"],
            "path": ".cursor/rules",
        },
        "agent_skills": _agent_skills_block(ctx),
        "legacy_skills_submodule_path": ".cursor/skills",
        "agents_template": agents_template,
        "pin_template": pin_template,
        "forbidden_paths": [
            "docs/specification/harness/",
            "docs/specification/as-built/testing-and-verification.md",
        ],
    }


def render_harness_config(ctx: OnboardingContext) -> str:
    profiles: dict[str, Any] = {
        "python-backend": _harness_profile(
            ctx,
            "python-backend",
            "templates/harness-pin.yaml",
            "templates/AGENTS.python.md",
            "python",
            "python-services-rules",
        ),
    }
    if any(r["profile"] == "frontend" for r in ctx.spec["repos"]):
        profiles["frontend"] = _harness_profile(
            ctx,
            "frontend",
            "templates/harness-pin.frontend.yaml",
            "templates/AGENTS.frontend.md",
            "frontend",
            "nextjs-bff-rules",
        )
    if any(r["profile"] == "data_platform" for r in ctx.spec["repos"]):
        profiles["data-platform"] = _harness_profile(
            ctx,
            "data-platform",
            "templates/harness-pin.data-platform.yaml",
            "templates/AGENTS.data-platform.md",
            "python",
            "data-platform-rules",
        )

    harness_repos: dict[str, Any] = {}
    for repo in ctx.spec["repos"]:
        profile = _HARNESS_PROFILE_MAP.get(repo["profile"])
        if not profile:
            continue
        harness_repos[repo["name"]] = {
            "profile": profile,
            "service_name": repo["name"],
            "conda_env": repo["name"],
            "verify_smoke": "poetry run python -m tests.verify.verify_all",
        }

    data = {
        "apiVersion": "launchpad/v1",
        "kind": "HarnessConfig",
        "org": ctx.org,
        "default_workspace": "..",
        "profiles": profiles,
        "repos": harness_repos,
    }
    return _dump(data)


def render_project_config(ctx: OnboardingContext) -> str:
    codebase = [r["name"] for r in ctx.spec["repos"]] + [ctx.meta_repo]
    data = {
        "org": ctx.org,
        "project_title": ctx.spec["project"]["name"],
        "status_columns": [
            "Backlog",
            "Spec/CR",
            "Ready",
            "In progress",
            "Verify",
            "In review",
            "Done",
        ],
        "fields": [
            {"name": "Initiative", "type": "TEXT"},
            {"name": "CR", "type": "TEXT"},
            {"name": "Codebase", "type": "SINGLE_SELECT", "options": codebase},
            {"name": "Spec path", "type": "TEXT"},
            {"name": "Verify command", "type": "TEXT"},
            {
                "name": "As-built",
                "type": "SINGLE_SELECT",
                "options": ["yes", "no", "N/A"],
            },
            {"name": "QA manifest", "type": "TEXT"},
        ],
        "repos": [r["name"] for r in ctx.spec["repos"]],
        "issue_types": {
            "required": True,
            "roles": {"epic": "Epic", "task": "Task"},
            "ensure": [
                {
                    "name": "Epic",
                    "color": "purple",
                    "description": "Platform epic / initiative container (parent issue)",
                }
            ],
        },
    }
    return _dump(data)


def render_wiki_config(ctx: OnboardingContext) -> str:
    data = {
        "apiVersion": "launchpad/v1",
        "kind": "WikiConfig",
        "org": ctx.org,
        "repo": ctx.meta_repo,
    }
    return _dump(data)


def render_verify_config(ctx: OnboardingContext) -> str:
    org = ctx.org
    data = {
        "apiVersion": "launchpad/v1",
        "kind": "VerifyManifest",
        "org": org,
        "includes": {
            "org": f"config/org-{org}.yaml",
            "gitflow": f"config/gitflow-{org}.yaml",
            "project": f"config/project-{org}.yaml",
        },
        "checks": [
            {"id": "org.access", "phase": "scopes", "required": True},
            {"id": "projects.api", "phase": "scopes", "required": True},
            {
                "id": "issue_types.api",
                "phase": "scopes",
                "required": True,
                "when": "project.issue_types_required",
            },
            {"id": "repos.present", "phase": "applied", "required": True, "repos_from": "org.repos"},
            {"id": "teams.present", "phase": "applied", "required": True, "teams_from": "org.teams"},
            {
                "id": "gitflow.develop",
                "phase": "applied",
                "required": True,
                "repos_from": "gitflow.repos",
            },
            {
                "id": "project.present",
                "phase": "applied",
                "required": True,
                "title_from": "project.project_title",
            },
            {
                "id": "issue_types.present",
                "phase": "applied",
                "required": True,
                "names_from": "project.issue_types_ensure",
            },
        ],
    }
    return _dump(data)


def render_playbook_readme(ctx: OnboardingContext) -> str:
    org = ctx.org
    name = ctx.display_name
    board = ctx.board_url
    lp = ctx.launchpad_playbook_base
    return f"""# {name} playbook (deltas only)

**Process SSOT:** [launchpad `playbook/`]({lp}) — SDD, harness, gitflow, PAT, PM process, wiki setup.

**This folder:** {name} / **{org}** specifics only — modules, board, teams, PM prompts, factory paths.

| | |
|--|--|
| **Org** | [{org}]({ctx.forge_host}/{org}) |
| **Factory** | `launchpad` + [`config/`](../config/) |
| **Board** | [{ctx.spec['project']['name']}]({board}) |

---

## Launchpad (generic process)

| Topic | Document |
|-------|----------|
| SDD workflow | [launchpad/sdd-workflow.md]({lp}/sdd-workflow.md) |
| Spec layout | [launchpad/spec-layout.md]({lp}/spec-layout.md) |
| Harness pins | [launchpad/harness-pins.md]({lp}/harness-pins.md) |
| PM workflow | [launchpad/pm-workflow.md]({lp}/pm-workflow.md) |
| Factory CLI | [launchpad/python-automation.md]({lp}/python-automation.md) |
| Wiki publish | [launchpad/wiki-setup.md]({lp}/wiki-setup.md) |

---

## {name} deltas (this repo)

Add `{org.lower()}-*.md` files here when process differs from launchpad — not before.
"""


def all_config_renders(ctx: OnboardingContext) -> dict[str, str]:
    org = ctx.org
    return {
        f"config/org-{org}.yaml": render_org_config(ctx),
        f"config/platform-{org}.yaml": render_platform_config(ctx),
        f"config/gitflow-{org}.yaml": render_gitflow_config(ctx),
        f"config/harness-{org}.yaml": render_harness_config(ctx),
        f"config/project-{org}.yaml": render_project_config(ctx),
        f"config/wiki-{org}.yaml": render_wiki_config(ctx),
        f"config/verify-platform-{org}.yaml": render_verify_config(ctx),
    }
