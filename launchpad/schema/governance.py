"""GovernanceConfig schema — GitHub org governance for a programme.

File: config/governance-<org>.yaml
Kind: GovernanceConfig

Fields
------
org             Must match programme.yaml org.
stack_profiles  Map of stack name → display label (YAML SSOT — kit merges nothing).
                Declare every stack you use; repos.stack must reference a key here.
teams           List of GitHub team definitions.
  name          Team slug on GitHub.
  description   Short description (optional).
  privacy       "closed" | "secret" (default: "closed").
repos           Map of repo slug → RepoEntry.
  stack         Required. Must be a key in stack_profiles.
  teams         Required. At least one team slug from teams[].
  visibility    "private" | "public" | "internal" (default: "private").
  description   Optional.
policy          Optional gitflow / branch-protection policy.
project_board   Optional GitHub Project board setup.
                Fields: enabled, name, number (int), url (https://github.com/orgs/.../projects/N).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from launchpad.schema.errors import SchemaError

API_VERSION = "launchpad/v1"
KIND = "GovernanceConfig"

_VALID_PRIVACY = {"closed", "secret"}
_VALID_VISIBILITY = {"private", "public", "internal"}


class TeamEntry:
    def __init__(self, raw: dict[str, Any], *, idx: int, path: str = "") -> None:
        name = str(raw.get("name") or "").strip()
        if not name:
            raise SchemaError(
                f"teams[{idx}] is missing required field 'name'", path=path
            )
        self.name = name
        self.description = str(raw.get("description") or "").strip()
        privacy = str(raw.get("privacy") or "closed").strip().lower()
        if privacy not in _VALID_PRIVACY:
            raise SchemaError(
                f"teams[{idx}] ({name!r}) has invalid privacy={privacy!r}",
                path=path,
                hint=f"Use one of: {sorted(_VALID_PRIVACY)}",
            )
        self.privacy = privacy


class RepoEntry:
    def __init__(
        self,
        name: str,
        raw: dict[str, Any],
        *,
        known_stacks: set[str],
        known_teams: set[str],
        path: str = "",
    ) -> None:
        stack = str(raw.get("stack") or "").strip()
        if not stack:
            raise SchemaError(
                f"repos.{name!r} missing required field 'stack'",
                path=path,
                hint=f"Add stack: <profile>.  Known profiles: {sorted(known_stacks)}",
            )
        if stack not in known_stacks:
            raise SchemaError(
                f"repos.{name!r} stack={stack!r} is not in stack_profiles",
                path=path,
                hint=f"Add {stack!r} to stack_profiles or use one of: {sorted(known_stacks)}",
            )
        self.name = name
        self.stack = stack

        teams = raw.get("teams") or []
        if not isinstance(teams, list) or len(teams) == 0:
            raise SchemaError(
                f"repos.{name!r} requires at least one team in 'teams'",
                path=path,
                hint="Set teams: [<team-slug>] — must reference entries in the teams: block",
            )
        unknown = [t for t in teams if t not in known_teams]
        if unknown:
            raise SchemaError(
                f"repos.{name!r} references unknown teams: {unknown}",
                path=path,
                hint=f"Declare them in the teams: block first",
            )
        self.teams: list[str] = list(teams)

        visibility = str(raw.get("visibility") or "private").strip().lower()
        if visibility not in _VALID_VISIBILITY:
            raise SchemaError(
                f"repos.{name!r} visibility={visibility!r} is invalid",
                path=path,
                hint=f"Use one of: {sorted(_VALID_VISIBILITY)}",
            )
        self.visibility = visibility
        self.description = str(raw.get("description") or "").strip()


class GovernanceSchema:
    """Validated, normalised representation of governance-<org>.yaml."""

    def __init__(self, raw: dict[str, Any], *, path: str = "") -> None:
        self._path = path
        self.org: str = ""
        self.stack_profiles: dict[str, str] = {}
        self.teams: list[TeamEntry] = []
        self.repos: dict[str, RepoEntry] = {}
        self.policy: dict[str, Any] = {}
        self.project_board: dict[str, Any] = {}
        self._validate(raw)

    def _validate(self, raw: dict[str, Any]) -> None:
        p = self._path

        org = str(raw.get("org") or "").strip()
        if not org:
            raise SchemaError(
                "governance YAML missing required field 'org'",
                path=p,
                hint="Set org: to match your programme.yaml org (e.g. 'apex-common')",
            )
        self.org = org

        stacks_raw = raw.get("stack_profiles") or {}
        if not isinstance(stacks_raw, dict):
            raise SchemaError("'stack_profiles' must be a mapping", path=p)
        self.stack_profiles = {k: str(v) for k, v in stacks_raw.items()}

        teams_raw = raw.get("teams") or []
        if not isinstance(teams_raw, list):
            raise SchemaError("'teams' must be a list", path=p)
        self.teams = [TeamEntry(t, idx=i, path=p) for i, t in enumerate(teams_raw)]
        known_teams = {t.name for t in self.teams}

        repos_raw = raw.get("repos") or {}
        if not isinstance(repos_raw, dict):
            raise SchemaError("'repos' must be a mapping", path=p)
        for repo_name, repo_data in repos_raw.items():
            if not isinstance(repo_data, dict):
                raise SchemaError(f"repos.{repo_name!r} must be a mapping", path=p)
            self.repos[repo_name] = RepoEntry(
                repo_name,
                repo_data,
                known_stacks=set(self.stack_profiles),
                known_teams=known_teams,
                path=p,
            )

        self.policy = dict(raw.get("policy") or {})
        pb_raw = raw.get("project_board") or {}
        if pb_raw and not isinstance(pb_raw, dict):
            raise SchemaError("'project_board' must be a mapping", path=p)
        self.project_board = dict(pb_raw)
        number_raw = self.project_board.get("number")
        if number_raw is not None and str(number_raw).strip() != "":
            try:
                self.project_board["number"] = int(number_raw)
            except (TypeError, ValueError) as exc:
                raise SchemaError(
                    "project_board.number must be an integer",
                    path=p,
                    hint="Example: number: 3",
                ) from exc

    @property
    def team_names(self) -> list[str]:
        return [t.name for t in self.teams]

    def as_dict(self) -> dict[str, Any]:
        return {
            "apiVersion": API_VERSION,
            "kind": KIND,
            "org": self.org,
            "stack_profiles": self.stack_profiles,
            "teams": [{"name": t.name, "description": t.description, "privacy": t.privacy} for t in self.teams],
            "repos": {
                name: {"stack": r.stack, "teams": r.teams, "visibility": r.visibility, "description": r.description}
                for name, r in self.repos.items()
            },
            "policy": self.policy,
            "project_board": self.project_board,
        }


def load_governance(path: str | Path) -> GovernanceSchema:
    """Load and validate a governance-<org>.yaml from *path*."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise SchemaError(f"Governance YAML not found: {p}")
    with p.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise SchemaError(f"Governance YAML must be a YAML mapping: {p}")
    return GovernanceSchema(raw, path=str(p))
