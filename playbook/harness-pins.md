# Harness pins (frozen surface)

Platform-owned constitution (rules submodule) and **prayog-skills** dev bundle. App repos **pin** rules; dev skills are **seeded** on sync.

---

## Repos

| Repo | Mount / path | Owner | Contents |
|------|----------------|-------|----------|
| `your-org/service-rules` (private) | `.cursor/rules/` submodule | Platform | `.mdc` constitution |
| [prayog-skills](https://github.com/drivestream-lab/prayog-skills) | `.agents/skills/` (seeded) | Public | Dev workflow skills |
| `<client>-meta` (private) | (tenant workspace) | Tenant | PRDs, manifests, factory config, templates |

---

## Recommended pin file (app repo root)

```yaml
# .harness-pin.yaml
profile: python-backend

rules:
  repo: your-org/service-rules
  ref: v1.0.0

agent_skills:
  repo: drivestream-lab/prayog-skills
  ref: v0.2.0
  skills:
    - spec-feasibility-review
    - spec-implementation-plan
    - pre-implement
    - verify
```

Bump via harness PR after platform publishes a new approved rules + skills pair.

---

## Approved pairs (examples)

Document your org's approved `rules` + `agent_skills` ref pairs in tenant `scripts/config/harness-<org>.yaml`.

| rules | agent_skills | Notes |
|-------|--------------|-------|
| v1.0.0 | v0.2.0 | Example python-backend pair |

---

## What sync-harness does

1. Write `.harness-pin.yaml` and `AGENTS.md`
2. Sync **rules** submodule @ pinned ref
3. Remove legacy **`.cursor/skills`** submodule if present
4. Seed prayog-skills dev bundle → `.agents/skills/`
5. Gitignore **`.agents/`**; optional commit **`skills-lock.json`**

**PM pipeline skills** (`validate-requirements`, `generate-work-manifest`, …) install in **`<client>-meta`** only — not app repos.

---

## Factory commands

From `<client>-meta`:

```bash
launchpad sync-harness --repo example-api --dry-run
launchpad sync-harness --repo example-api --apply
launchpad verify-harness
```

Config: `scripts/config/harness-<org>.yaml`

**Onboard a new app repo:**

1. Add entry under `repos:` in harness config.
2. Clone repo next to `<client>-meta` (see `default_workspace` in harness config).
3. `launchpad sync-harness --repo <name> --apply`
4. Commit pin, `AGENTS.md`, rules submodule, `.gitignore` (`.agents/`).
5. `launchpad verify-harness --repo <name>` before opening PR.

---

## Related

- [pm-workflow.md](pm-workflow.md)
- [spec-layout.md](spec-layout.md)
- [prayog-skills](https://github.com/drivestream-lab/prayog-skills)
