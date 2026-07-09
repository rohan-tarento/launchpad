# Harness pins (frozen surface)

Platform-owned constitution (rules submodule) and **prayog-skills** dev bundle. App repos **pin** rules; dev skills are **seeded** on sync.

---

## Repos

| Repo | Mount / path | Owner | Contents |
|------|----------------|-------|----------|
| `drivestream-lab/python-services-rules` | `.cursor/rules/` submodule | Platform (OSS) | `.mdc` constitution |
| [prayog-skills](https://github.com/drivestream-lab/prayog-skills) | `.agents/skills/` (seeded) | Public | Dev workflow skills |
| `<client>-meta` (private) | (tenant workspace) | Tenant | PRDs, manifests, factory config, templates |

---

## Constitution vs router vs skills (do not mix layers)

| Layer | Location | Contains | SSOT for changes |
|-------|----------|----------|------------------|
| **Constitution** | `.cursor/rules/*.mdc` (rules submodule) | How to code — SDD discipline, patterns, boundaries | `drivestream-lab/*-rules` repo |
| **Router** | `AGENTS.md` | Harness pin, verify commands, playbook links, **which** skills exist | Harness sync templates + tenant overrides |
| **Procedures** | `.agents/skills/` (gitignored) | Step-by-step slash workflows (`/pre-implement`, `/verify`, …) | [prayog-skills](https://github.com/drivestream-lab/prayog-skills) @ pinned ref |

**Never** enumerate prayog skill names or slash commands in `*-rules` MDC files — they drift from `AGENTS.md` and prayog. Rules repos run `scripts/check_mdc_boundary.sh` in CI to enforce this.

---

## Recommended pin file (app repo root)

```yaml
# .harness-pin.yaml
profile: python-backend

rules:
  repo: drivestream-lab/python-services-rules
  ref: v0.5.5

agent_skills:
  repo: drivestream-lab/prayog-skills
  ref: v0.4.0
  profile: python-backend
  skills:
    - spec-draft
    - initiative-feasibility
    - spec-technical-review
    - spec-implementation-plan
    - pre-implement
    - loop-spec
    - ground-spec
    - verify
```

`skills` in the pin file are **resolved at sync** from prayog @ `ref` (SSOT: `profiles/python-backend.yaml` or meta-pm tree convention). Tenant harness config only pins `repo`, `url`, `ref`, and `profile`.

---

## Approved pairs (examples)

Document your org's approved `rules` + `agent_skills` ref pairs in tenant `config/harness-<org>.yaml`.

| rules | agent_skills | Notes |
|-------|--------------|-------|
| v0.5.5 | v0.4.0 | Current — python-services-rules (python-backend) |
| v0.3.0 | v0.4.0 | Current — data-platform-rules (data-platform profile) |
| v0.1.1 | v0.4.0 | Current — nextjs-bff-rules (frontend profile) |
| v0.5.5 | v0.3.1 | Superseded — previous python-backend pin |
| v0.5.5 | v0.2.0 | Superseded — 4-skill dev bundle |

Bump via harness PR after platform publishes a new approved rules + skills pair.

---

## What apply-harness does

1. Write `.harness-pin.yaml` and `AGENTS.md`
2. Sync **rules** submodule @ pinned ref
3. Remove legacy **`.cursor/skills`** submodule if present
4. Seed prayog-skills dev bundle → `.agents/skills/`
5. Gitignore **`.agents/`**; optional commit **`skills-lock.json`**

**PM pipeline skills** (`validate-requirements`, `prd-impact-map`, …) install in **`<slug>-meta`** only — not app repos.

---

## Factory commands

Submodule URLs in harness config must use **HTTPS** (`rules.url`, `agent_skills.url`). SSH URLs are rejected — fix the harness YAML if sync fails.

From the `<slug>-meta` config directory:

```bash
launchpad apply-harness --repo example-api --dry-run
launchpad apply-harness --repo example-api --apply
launchpad status --repo example-api
```

Config: `config/harness-<org>.yaml`

Template paths resolve **tenant override first**, then **launchpad kit** `templates/` (pipx install). Store only tenant-specific overrides under `<slug>-meta/templates/`.

**Onboard a new app repo:** see [greenfield-app-repo.md](greenfield-app-repo.md).

Short harness-only path (repo already exists with code):

1. Add entry under `repos:` in `harness-<org>.yaml`.
2. Ensure clone lives next to `<slug>-meta` in the workspace.
3. `launchpad apply-harness --repo <name> --apply`
4. Commit pin, `AGENTS.md`, rules submodule, `.gitignore` (`.agents/`).
5. `launchpad status --repo <name>` before opening PR.

---

## Meta repo (`apply-harness --meta`)

PM workspace — no rules submodule. Installs prayog PM skills + community `prd` (awesome-copilot).

```bash
launchpad apply-harness --meta --dry-run
launchpad apply-harness --meta --apply
launchpad status --meta
```

Commit `.harness-pin.yaml`, `skills-lock.json`, `AGENTS.md` — **not** `.agents/skills/` (gitignored).

Meta structure comes from `apply-scaffold --meta` (cookiecutter `tenant-meta-foundation`).

---

## Related

- [pm-workflow.md](pm-workflow.md)
- [spec-layout.md](spec-layout.md)
- [prayog-skills](https://github.com/drivestream-lab/prayog-skills)
