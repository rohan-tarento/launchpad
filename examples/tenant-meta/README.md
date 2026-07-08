# Example tenant meta (smoke fixture)

This directory is the canonical example of a `<slug>-meta` control-plane repo.
It is also used for local smoke tests (`LAUNCHPAD_TENANT_ROOT=examples/tenant-meta`).

---

## Config files

All five YAML kinds live in `config/`:

| File | Kind | Purpose |
|---|---|---|
| `programme.yaml` | Programme | Identity spine: name, slug, org, workspace, forge |
| `governance-example-org.yaml` | GovernanceConfig | Teams, repos (stack + teams required), gitflow policy, board |
| `harness-example-org.yaml` | HarnessConfig | Constitution (rules submodule) + agent skills per stack profile |
| `scaffold-example-org.yaml` | ScaffoldConfig | Cookiecutter sources per repo (free-form context pass-through) |
| `service-catalog-example-org.yaml` | ServiceCatalog | Service map (required; meta live + app examples commented) |

Rename `*-example-org.yaml` → `*-<your-org>.yaml` in your real meta repo.

---

## Greenfield setup

The interview generates all five files automatically:

```bash
launchpad onboard interview
```

Then:

```bash
# Day 1: meta repo on GitHub
launchpad init-client --meta --dry-run    # preview
launchpad init-client --meta --apply      # execute

# Day 1: scaffold (optional)
# Edit config/scaffold-<org>.yaml: set meta.enabled: true
launchpad apply-scaffold --meta --apply

# Day 1: pin harness
launchpad apply-harness --meta --apply
launchpad check-harness --meta

# Day N: app repos (edit governance + scaffold YAMLs first)
launchpad init-client    --repo example-api --apply
launchpad apply-scaffold --repo example-api --apply
launchpad apply-harness  --repo example-api --apply
```

All commands are **dry-run by default** — pass `--apply` to execute.

---

## Directory layout

| Path | Purpose |
|---|---|
| `config/` | All five factory YAMLs (programme, governance, harness, scaffold, catalog) |
| `prd/` | Product requirements (`INIT-*.md`) after PM sign-off |
| `planning/` | Pre-build narratives — not app-repo SSOT |
| `programs/` | Programme overviews |
| `work/` | `WorkManifest` YAML → `launchpad seed-work` |
| `wiki/` | Published to GitHub Wiki via `launchpad publish-wiki` |
| `playbook/` | Client-specific playbook deltas (kit playbook is the SSOT) |
| `templates/` | Client-specific template overrides (kit defaults apply otherwise) |

**No `.env` in meta** — factory secrets live in `~/.config/launchpad/env.d/<slug>.env` only.

---

## Further reading

- [docs/greenfield.md](../../docs/greenfield.md) — Day-0 → Day-N walkthrough
- [docs/SCHEMA.md](../../docs/SCHEMA.md) — 5 YAML kinds reference
- [docs/stacks.md](../../docs/stacks.md) — Stack registry + adding custom stacks
