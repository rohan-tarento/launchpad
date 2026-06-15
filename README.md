# Launchpad

**Specification-driven development (SDD)** and **harness engineering** for multi-client engineering orgs — with a YAML-driven forge factory on top.

Launchpad is not primarily a “create GitHub repos” script. It is a repeatable kit for running product delivery where **specs are truth**, **agents have a pinned constitution**, and **factory automation enforces the process** (gitflow, board, backlog seeding).

Agent skills: **[prayog-skills](https://github.com/drivestream-lab/prayog-skills)**.  
MDC / rules repos stay **private** and are **pinned** per app repo via harness config.

---

## What we're actually doing

Most teams bolt AI on top of ad-hoc repos. Launchpad inverts that:

| Pillar | What it means | Where it lives |
|--------|---------------|----------------|
| **SDD** | **What** to build (`product/`), **what is live** (`as-built/`), **why** (`adr/`) — read before code changes | App repos + `<client>-meta` PRDs |
| **Harness engineering** | Frozen agent surface: rules submodule, `AGENTS.md`, prayog-skills bundle, verify discipline | `.harness-pin.yaml` + `sync-harness` |
| **Factory** | GitHub/GitLab bootstrap, gitflow policy, project board, work manifests → issues | `launchpad` CLI + tenant `scripts/config/*.yaml` |

```text
PM lane (<client>-meta)          Dev lane (app repos)
────────────────────────         ────────────────────
prd/ INIT PRDs                   docs/specification/product/
work/ manifests                  docs/specification/as-built/
planning/ (pre-build archive)    docs/specification/adr/
        │                                │
        │  seed-work                     │  sync-harness
        ▼                                ▼
   GitHub/GitLab board              rules + skills + AGENTS.md
        │                                │
        └──────── SDD handoff ───────────┘
                    PR traceability (INIT, spec paths, verify)
```

Deep dives: [SDD workflow](playbook/sdd-workflow.md) · [Spec layout](playbook/spec-layout.md) · [Harness pins](playbook/harness-pins.md) · [PM workflow](playbook/pm-workflow.md)

---

## Specification-driven development (SDD)

**Read order for every change** (agents and humans):

1. **Constitution** — `.cursor/rules/*.mdc` (private rules submodule)
2. **`AGENTS.md`** — router, verify commands, harness pin
3. **`docs/specification/product/`** — what to build
4. **`docs/specification/adr/`** — accepted decisions
5. **`docs/specification/as-built/`** — what is live today (do not assume from product spec alone)

**PM owns narrative truth** in `<client>-meta` (`prd/`, `planning/`, `work/`). **Dev owns implementation truth** in app repos (product spec updates, as-built, tests, verify). Long-form pre-build planning stays in meta — not scattered in app repos.

Every PR ties back to an **INIT**, issue #, **spec paths touched**, and **verify command run**.

---

## Harness engineering

The **harness** is the frozen agent + verify surface for each app repo:

```yaml
# .harness-pin.yaml (generated/managed by launchpad sync-harness)
profile: python-backend

rules:
  repo: your-org/service-rules   # private — .mdc constitution
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

`sync-harness` writes the pin, `AGENTS.md`, rules submodule, and seeds prayog-skills into `.agents/skills/`. `verify-harness` checks the repo matches tenant harness config.

**PM pipeline skills** (`validate-requirements`, `generate-work-manifest`, …) run in **`<client>-meta` only**. **Dev skills** run in **app repos** after harness sync.

---

## Repo layers

| Layer | Repo | Visibility | Role |
|-------|------|------------|------|
| Kit | **launchpad** (this repo) | Public | Playbook, CLI, templates, tenant skeleton |
| Skills | [prayog-skills](https://github.com/drivestream-lab/prayog-skills) | Public | Dev + PM agent skills |
| Tenant | `<client>-meta` | Private | PRDs, planning, wiki, factory + harness YAML |
| Constitution | `your-org/*-rules` | Private | MDC rules — pinned, never copied into launchpad |

---

## Quick start (local, no pip)

```bash
cd ~/Workspace/handson/launchpad
python3 -m venv .venv && .venv/bin/pip install -e .

export LAUNCHPAD_TENANT_ROOT=~/Workspace/handson/launchpad/examples/tenant-meta
./scripts/smoke-local.sh          # doctor + seed-work dry-run (no token)
./bin/launchpad doctor
```

See [docs/local-dev.md](docs/local-dev.md) for testing against your own `<client>-meta`.  
**New client setup:** [docs/setup-guide.md](docs/setup-guide.md) · [docs/new-client.md](docs/new-client.md)

---

## Tenant layout (`<client>-meta`)

Each private tenant repo holds **real product content** (not shipped in launchpad):

| Path | Purpose |
|------|---------|
| `prd/` | INIT PRDs and validation reports |
| `planning/` | Pre-build archive (not app-repo SSOT) |
| `programs/` | Programme overviews |
| `work/` | WorkManifest YAML → `launchpad seed-work` |
| `wiki/` | Client wiki |
| `scripts/config/` | Org factory YAML (gitflow policy is **authoritative** here) |

Empty skeleton: [`examples/tenant-meta/`](examples/tenant-meta/).  
Worked example: [`examples/diet_coke-meta/`](examples/diet_coke-meta/) (org `kd_diet_coke`, repos `diet_coke-api`, `diet_coke-bff`, `diet_coke-registry`).

---

## CLI (factory + harness)

Run from `<client>-meta` (or set `LAUNCHPAD_TENANT_ROOT`):

```bash
# Harness (no GitHub API — works offline for sync/verify)
launchpad sync-harness --repo example-api --apply
launchpad verify-harness --repo example-api

# Factory (GitHub v1 — needs GITHUB_TOKEN)
launchpad setup-platform --config scripts/config/platform-<org>.yaml --apply
launchpad setup-gitflow --config scripts/config/gitflow-<org>.yaml --apply
launchpad seed-work --config work/INIT-*.yaml --apply
```

Gitflow **branch naming, merge policy, PR rules, and CI gates** are declared only in `gitflow-<org>.yaml` — not on the CLI.

Full command reference: [playbook/python-automation.md](playbook/python-automation.md).

---

## Forges

| Forge | Status |
|-------|--------|
| GitHub | **v1** — full factory (org, teams, gitflow, project, seed-work) |
| GitLab | **partial** — `seed-work` + scoped labels |

---

## Docs

| Document | Purpose |
|----------|---------|
| [docs/setup-guide.md](docs/setup-guide.md) | **End-to-end setup** — hypothetical diet_coke project (`kd_diet_coke`) |
| [docs/new-client.md](docs/new-client.md) | Onboarding checklist |
| [playbook/sdd-workflow.md](playbook/sdd-workflow.md) | SDD truth hierarchy and PR discipline |
| [playbook/spec-layout.md](playbook/spec-layout.md) | Mandatory `docs/specification/` layout |
| [playbook/harness-pins.md](playbook/harness-pins.md) | Harness pin format and sync workflow |
| [playbook/pm-dev-handoff.md](playbook/pm-dev-handoff.md) | PM ↔ dev lanes and merge rules |
| [playbook/README.md](playbook/README.md) | Full playbook index |
| [docs/local-dev.md](docs/local-dev.md) | Source / `bin/launchpad` local testing |
| [docs/SCHEMA.md](docs/SCHEMA.md) | `launchpad/v1` YAML kinds |

---

## Schema

Config and manifests use `apiVersion: launchpad/v1`. Legacy `meta.meta/v1` manifests are accepted during migration.

---

## License

MIT — see [LICENSE](LICENSE).
