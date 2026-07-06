# Launchpad

**Specification-driven development (SDD)** and **harness engineering** for multi-client engineering orgs — with a YAML-driven forge factory on top.

Launchpad is not primarily a “create GitHub repos” script. It is a repeatable kit for running product delivery where **specs are truth**, **agents have a pinned constitution**, and **factory automation enforces the process** (gitflow, board, backlog seeding).

Agent skills: **[prayog-skills](https://github.com/drivestream-lab/prayog-skills)**.  
MDC / rules repos ([python-services-rules](https://github.com/drivestream-lab/python-services-rules), [nextjs-bff-rules](https://github.com/drivestream-lab/nextjs-bff-rules), [data-platform-rules](https://github.com/drivestream-lab/data-platform-rules)) are **public**, **pinned** per app repo via harness config — never copied into launchpad.

---

## Quick mental model

> **Launchpad = Terraform for engineering orgs + a playbook for how humans and agents deliver software together.**

- **CLI** — provisions forge infrastructure from YAML (repos, gitflow, board, backlog)
- **Playbook** — how PRDs become specs → board issues → merged PRs
- **Tenant meta** — client-specific product truth (`prd/`, `work/`, factory config)
- **Harness pins** — frozen agent constitution + skills in every app repo

---

## What we're actually doing

Most teams bolt AI on top of ad-hoc repos. Launchpad inverts that:

| Pillar | What it means | Where it lives |
|--------|---------------|----------------|
| **SDD** | **What** to build (`product/`), **what is live** (`as-built/`), **why** (`adr/`) — read before code changes | App repos + `<client>-meta` PRDs |
| **Harness engineering** | Frozen agent surface: rules submodule (apps), PM skills (meta), `AGENTS.md`, prayog bundle | `.harness-pin.yaml` + `sync-harness-app` / `sync-harness-meta` |
| **Factory** | GitHub/GitLab bootstrap, gitflow policy, project board, work manifests → issues | `launchpad` CLI + tenant `config/*.yaml` |

```text
PM lane (<client>-meta)          Dev lane (app repos)
────────────────────────         ────────────────────
prd/ INIT PRDs                   docs/specification/product/
work/ manifests                  docs/specification/as-built/
planning/ (pre-build archive)    docs/specification/adr/
        │                                │
        │  seed-work                     │  sync-harness-meta / sync-harness-app
        ▼                                ▼
   GitHub/GitLab board              rules + skills + AGENTS.md
        │                                │
        └──────── SDD handoff ───────────┘
                    PR traceability (INIT, spec paths, verify)
```

Deep dives: [SDD workflow](playbook/sdd-workflow.md) · [Spec layout](playbook/spec-layout.md) · [Harness pins](playbook/harness-pins.md) · [Greenfield app repo](playbook/greenfield-app-repo.md) · [PM workflow](playbook/pm-workflow.md)

---

## Specification-driven development (SDD)

**Read order for every change** (agents and humans):

1. **Constitution** — `.cursor/rules/*.mdc` (rules submodule @ pinned ref)
2. **`AGENTS.md`** — router, verify commands, harness pin
3. **`docs/specification/product/`** — what to build
4. **`docs/specification/adr/`** — accepted decisions
5. **`docs/specification/as-built/`** — what is live today (do not assume from product spec alone)

**PM owns narrative truth** in `<client>-meta` (`prd/`, `planning/`). **Dev owns implementation truth** in app repos (product spec, as-built, tests, verify). **`work/INIT-*.yaml`** is dev-generated (plan §9) for product INITs — PM merges only when bulk `seed-work` is used. Long-form pre-build planning stays in meta — not scattered in app repos.

Every PR ties back to an **INIT**, issue #, **spec paths touched**, and **verify command run**.

---

## Harness engineering

The **harness** is the frozen agent + verify surface for each app repo:

```yaml
# .harness-pin.yaml (generated/managed by launchpad sync-harness-app or sync-harness-meta)
profile: python-backend

rules:
  repo: drivestream-lab/python-services-rules   # .mdc constitution submodule
  ref: v0.5.5

agent_skills:
  repo: drivestream-lab/prayog-skills
  ref: v0.4.0
  profile: python-backend
  skills:
    - spec-draft
    - initiative-feasibility
    - spec-implementation-plan
    - pre-implement
    - loop-spec
    - ground-spec
    - verify
```

`sync-harness-app` writes the pin, `AGENTS.md`, rules submodule, and seeds dev prayog skills into `.agents/skills/`. `sync-harness-meta` does the same for PM skills in tenant meta (no rules submodule). `verify-harness-app` / `verify-harness-meta` check repos match tenant harness config.

**PM pipeline skills** (`validate-requirements`, `prd-impact-map`, …) run in **`<client>-meta` only**. **Dev skills** (including board seed via `/spec-implementation-plan` §9) run in **app repos** after harness sync.

---

## Repo layers

| Layer | Repo | Visibility | Role |
|-------|------|------------|------|
| Kit | **launchpad** (this repo) | Public | Playbook, CLI, templates, tenant skeleton |
| Skills | [prayog-skills](https://github.com/drivestream-lab/prayog-skills) | Public | Dev + PM agent skills |
| Foundations | [python-fastapi-foundation](https://github.com/drivestream-lab/python-fastapi-foundation), [tenant-meta-foundation](https://github.com/drivestream-lab/tenant-meta-foundation) | Public | Cookiecutter scaffolds for app + meta repos |
| Constitution | [python-services-rules](https://github.com/drivestream-lab/python-services-rules), [nextjs-bff-rules](https://github.com/drivestream-lab/nextjs-bff-rules), [data-platform-rules](https://github.com/drivestream-lab/data-platform-rules) | Public | MDC rules — pinned submodule, never copied into launchpad |
| Tenant | `<client>-meta` | Private (per customer) | PRDs, planning, wiki, factory + harness YAML |

---

## Install (operators)

Once per machine — run factory commands from anywhere:

```bash
git clone https://github.com/drivestream-lab/launchpad.git ~/Workspace/handson/launchpad
cd ~/Workspace/handson/launchpad
pipx install -e .

# One-time client registry — see docs/multi-laptop.md
launchpad clients
launchpad doctor
```

Greenfield and incremental repo flows: see **Workflows** below.

Full walkthrough: [docs/setup-guide.md](docs/setup-guide.md) · [docs/multi-laptop.md](docs/multi-laptop.md)

---

## Workflows

Run all commands from **`<client>-meta`** (after `clients.yaml` + `env.d/<client>.env` are set). Default is **`--dry-run`**; add **`--apply`** to execute.

**Workspace layout** (default `options.workspace: ..` in gitflow YAML):

```text
~/Workspace/<client>/
  <client>-meta/     # tenant meta — run launchpad here
  example-api/       # app clones (siblings of meta)
  example-registry/
```

### A — Greenfield (new client / new org)

First-time bootstrap: onboarding spec → local meta → GitHub factory → local clones → app scaffolding.

| Step | What | Command |
|------|------|---------|
| 1 | Install kit + registry | `pipx install -e .` · see [multi-laptop.md](docs/multi-laptop.md) |
| 2 | Plan tenant | `launchpad onboard plan --spec ~/Workspace/handson/<client>/onboarding.yaml` |
| 3 | Render factory YAML | `launchpad onboard apply --spec …/onboarding.yaml` (config + templates only) |
| 4 | Meta layout stubs | `launchpad --client <client> scaffold-meta --apply --force` (prd/, work/, wiki/ — preserves config/) |
| 5 | Paste forge token | edit `~/.config/launchpad/env.d/<client>.env` |
| 6 | Platform baseline | `launchpad --client <client> setup-platform --config config/platform-<org>.yaml --apply` |

`setup-platform --apply` runs in order:

```text
bootstrap-org → bootstrap-teams → seed-repos → clone-repos → setup-gitflow → bootstrap-project → sync-catalog
```

Creates GitHub repos, seeds `develop`, **clones locally** (greenfield meta keeps onboard content over factory seed), applies gitflow + board, writes `config/service-catalog-<org>.yaml`.

| Step | What | Command |
|------|------|---------|
| 7 | Curate service catalog | edit `config/service-catalog-<org>.yaml` (`owns`, `depends_on`, `branch_code`) |
| 8 | Push meta to GitHub | commit meta → PR to `<client>-meta/develop` |
| 9 | Harness meta | `launchpad sync-harness-meta --apply` |
| 10 | Scaffold each app | `launchpad scaffold-app --repo <app> --apply --force` (into existing clone) |
| 11 | Harness each app | `launchpad sync-harness-app --repo <app> --apply` |
| 12 | Backlog | PRD → dev plan §9 → `gh issue create` (optional `launchpad seed-work` multi-repo) |

Wizard details: [docs/onboarding-wizard.md](docs/onboarding-wizard.md) · App repo deep dive: [playbook/greenfield-app-repo.md](playbook/greenfield-app-repo.md)

### B — Ongoing project (add a new app repo)

When the org already exists and you are adding repo **N+1** incrementally:

| Step | What | Where |
|------|------|-------|
| 1 | Register repo | edit `config/org-<org>.yaml`, `gitflow-<org>.yaml`, `harness-<org>.yaml` |
| 2 | Commit meta | PR meta config to `<client>-meta/develop` |

Then from `<client>-meta`:

```bash
launchpad bootstrap-org --apply                    # create GitHub repo if missing
launchpad seed-repos --repo <new-app> --apply     # main + develop on GitHub
launchpad clone-repos --repo <new-app> --apply    # local clone on develop
launchpad setup-gitflow --repo <new-app> --apply  # protection + templates
launchpad sync-catalog --apply                    # merge into service-catalog (keeps curated fields)
```

Curate the new entry in `config/service-catalog-<org>.yaml`, then scaffold:

```bash
launchpad scaffold-app --repo <new-app> --apply --force
launchpad sync-harness-app --repo <new-app> --apply
launchpad verify-harness-app --repo <new-app>
```

**Meta YAML is SSOT** — launchpad does not auto-edit org/gitflow/harness when you scaffold. Add the repo to config first, then run the commands above.

---

## Hack on launchpad (contributors)

```bash
cd ~/Workspace/handson/launchpad
python3 -m venv .venv && .venv/bin/pip install -e .

export LAUNCHPAD_TENANT_ROOT=~/Workspace/handson/launchpad/examples/tenant-meta
./scripts/smoke-local.sh          # doctor + seed-work dry-run (no token)
./bin/launchpad doctor
```

See [docs/local-dev.md](docs/local-dev.md) for source testing against your own `<client>-meta`.

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
| `config/` | Org factory YAML (gitflow policy is **authoritative** here) |
| `config/service-catalog-{org}.yaml` | Repo → team, branch_code, owns/depends_on (maintained by launchpad) |

Tenant skeleton: [`examples/tenant-meta/`](examples/tenant-meta/) — copy per client; rename `example-org` / `example-api` in YAML to your forge.

See **Workflows** above for greenfield vs incremental repo steps.

---

## CLI reference

Run from `<client>-meta`, or configure clients once in `~/.config/launchpad/` (see [docs/multi-laptop.md](docs/multi-laptop.md)):

```bash
launchpad clients                   # list configured clients
launchpad doctor                    # uses default client
launchpad --client drivestream doctor

# Harness (local clones — scaffold-app / sync-harness-* need these)
launchpad clone-repos --dry-run
launchpad clone-repos --apply
launchpad sync-harness-meta --apply
launchpad verify-harness-meta
launchpad scaffold-app --repo example-api --dry-run
launchpad scaffold-app --repo example-api --option has_kafka=yes --apply --force
launchpad sync-harness-app --repo example-api --apply
launchpad verify-harness-app --repo example-api
launchpad publish-wiki --apply

# Factory (GitHub v1 — needs GITHUB_TOKEN)
launchpad setup-platform --config config/platform-<org>.yaml --apply
launchpad seed-repos --config config/gitflow-<org>.yaml --apply
launchpad setup-gitflow --config config/gitflow-<org>.yaml --apply
launchpad sync-catalog --apply
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
| [docs/setup-guide.md](docs/setup-guide.md) | **End-to-end setup** — copy `tenant-meta`, customize for your org |
| [docs/new-client.md](docs/new-client.md) | Onboarding checklist |
| [docs/onboarding-wizard.md](docs/onboarding-wizard.md) | `onboard plan` / `onboard apply` from `onboarding.yaml` |
| [playbook/sdd-workflow.md](playbook/sdd-workflow.md) | SDD truth hierarchy and PR discipline |
| [playbook/spec-layout.md](playbook/spec-layout.md) | Mandatory `docs/specification/` layout |
| [playbook/harness-pins.md](playbook/harness-pins.md) | Harness pin format and sync workflow |
| [playbook/delivery-workflow.md](playbook/delivery-workflow.md) | **How we ship** — two-PR model, skills, merge gates |
| [playbook/README.md](playbook/README.md) | Full playbook index |
| [docs/multi-laptop.md](docs/multi-laptop.md) | **Client registry** — install + `clients.yaml` + `env.d` |
| [docs/local-dev.md](docs/local-dev.md) | Kit contributors — venv / source testing |

---

## Schema

All config and manifests use **`apiVersion: launchpad/v1`**. See [docs/SCHEMA.md](docs/SCHEMA.md) for `kind` types (`OrgConfig`, `GitflowConfig`, `ServiceCatalog`, `PlatformManifest`, …).

---

## License

MIT — see [LICENSE](LICENSE).
