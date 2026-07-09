"""Greenfield schema definitions and validators for v0.5.10.

Five YAML kinds:
  Programme       — identity spine (programme, org, meta_repo, workspace, forge)
  GovernanceConfig — GitHub: teams, repos, gitflow, project board
  HarnessConfig   — stack profiles (constitution + skills) + per-repo bindings
  ScaffoldConfig  — cookiecutter sources per repo (template, ref, context)
  ServiceCatalog  — service map (required; meta live + app examples)
"""

from launchpad.schema.programme import ProgrammeSchema, load_programme
from launchpad.schema.governance import GovernanceSchema, load_governance
from launchpad.schema.harness import HarnessSchema, load_harness
from launchpad.schema.scaffold import ScaffoldSchema, load_scaffold
from launchpad.schema.catalog import CatalogSchema, load_catalog
from launchpad.schema.errors import SchemaError

__all__ = [
    "ProgrammeSchema",
    "GovernanceSchema",
    "HarnessSchema",
    "ScaffoldSchema",
    "CatalogSchema",
    "SchemaError",
    "load_programme",
    "load_governance",
    "load_harness",
    "load_scaffold",
    "load_catalog",
]
