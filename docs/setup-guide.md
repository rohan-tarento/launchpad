# Setup guide — hypothetical **diet_coke** project

End-to-end onboarding for a new client using Launchpad. This walkthrough uses a **fictional** GitHub org and repos; adapt names to your forge.

| Concept | Example value |
|---------|----------------|
| Project slug | `diet_coke` |
| GitHub org | `kd_diet_coke` |
| Tenant meta repo | `diet_coke-meta` |
| Workspace folder | `~/Workspace/handson/diet_coke/` |

**Important:** Launchpad (the kit) and `diet_coke-meta` (the tenant) are **separate repos**. You install Launchpad once; you copy or create `diet_coke-meta` per client.

Reference configs: [`examples/diet_coke-meta/`](../examples/diet_coke-meta/).

---

## Architecture

```text
~/Workspace/handson/
├── launchpad/                    # public kit — CLI, playbook, templates (clone once)
└── diet_coke/                    # client workspace
    ├── diet_coke-meta/           # private tenant — PRDs, work/, scripts/config/
    ├── diet_coke-api/            # app repo (sibling clone)
    ├── diet_coke-bff/
    └── diet_coke-registry/
```

| Repo | Role |
|------|------|
| **launchpad** | Factory CLI + process playbook — **not** copied into meta |
| **diet_coke-meta** | Product lane — PRDs, manifests, factory YAML, wiki source |
| **diet_coke-api**, **diet_coke-bff**, … | Dev lane — specs, code, harness pin |

See also: [new-client.md](new-client.md) (checklist) · [local-dev.md](local-dev.md) (run from source).

---

## Phase 0 — Prerequisites (manual)

1. **GitHub org** `kd_diet_coke` exists (org admin access).
2. **GitHub Team** plan if you need branch protection on **private** repos.
3. **Private rules repo** (e.g. `your-org/diet_coke-rules`) with `.mdc` constitution — harness will submodule it into app repos.
4. **Fine-grained PAT** for factory automation — see [playbook/bootstrap-prerequisites.md](../playbook/bootstrap-prerequisites.md):
   - Org permissions: Administration, Members, Projects, **Issue types** (read/write)
   - Repository access: **All repositories** in `kd_diet_coke` (recommended)
   - Repo permissions: Administration, Contents, Issues, Metadata

`gh auth login` is for day-to-day PRs. The factory uses **`GITHUB_TOKEN`** in meta `.env` — `gh auth token` alone is **not** enough for project/issue-types bootstrap.

---

## Phase 1 — Install Launchpad (once per machine)

```bash
git clone https://github.com/drivestream-lab/launchpad.git ~/Workspace/handson/launchpad
cd ~/Workspace/handson/launchpad
python3 -m venv .venv && .venv/bin/pip install -e .
```

Or: `pipx install git+https://github.com/drivestream-lab/launchpad.git`

Verify:

```bash
export LAUNCHPAD_TENANT_ROOT=~/Workspace/handson/launchpad/examples/tenant-meta
~/Workspace/handson/launchpad/bin/launchpad doctor
~/Workspace/handson/launchpad/scripts/smoke-local.sh
```

---

## Phase 2 — Create `diet_coke-meta` (tenant)

Copy the example skeleton (or generic [`examples/tenant-meta/`](../examples/tenant-meta/)):

```bash
mkdir -p ~/Workspace/handson/diet_coke
cp -r ~/Workspace/handson/launchpad/examples/diet_coke-meta \
      ~/Workspace/handson/diet_coke/diet_coke-meta
cd ~/Workspace/handson/diet_coke/diet_coke-meta
git init
git remote add origin git@github.com:kd_diet_coke/diet_coke-meta.git
```

Create the **empty** `diet_coke-meta` repo on GitHub first (UI or `gh repo create kd_diet_coke/diet_coke-meta --private`), then push:

```bash
git add .
git commit -m "chore: initial diet_coke-meta tenant skeleton"
git push -u origin main
```

`diet_coke-meta` is **not** created by `bootstrap-org` — it is the repo you work in. Factory YAML lists **app repos** only.

Pin expected Launchpad version (already in skeleton):

```text
.launchpad-version → 0.1.0
```

---

## Phase 3 — Configure factory YAML

All files live in `diet_coke-meta/scripts/config/`. The example uses org slug **`kd_diet_coke`** in filenames.

| File | Purpose |
|------|---------|
| `org-kd_diet_coke.yaml` | Repos to create + org labels |
| `gitflow-kd_diet_coke.yaml` | Branch/merge/PR policy (**authoritative** — no CLI flags) |
| `platform-kd_diet_coke.yaml` | Orchestrates full factory bootstrap |
| `project-kd_diet_coke.yaml` | GitHub Project board + fields |
| `verify-platform-kd_diet_coke.yaml` | Post-bootstrap checks |
| `harness-kd_diet_coke.yaml` | Rules + prayog-skills pins per app repo |

Sample app repos under **diet_coke**:

| Repo | Profile | Notes |
|------|---------|-------|
| `diet_coke-api` | backend | Core API |
| `diet_coke-bff` | frontend | BFF / portal |
| `diet_coke-registry` | backend | Service registry |

In `harness-kd_diet_coke.yaml`, set `rules.repo` to **your private** rules repository and pin `ref`.

In `gitflow-kd_diet_coke.yaml`, set `options` for your rollout phase (see [playbook/github-enforcement.md](../playbook/github-enforcement.md)):

```yaml
options:
  require_ci: false      # true after workflow PRs merged
  branch_naming: true
  with_templates: true
  init_empty: true       # only for brand-new empty repos
  workspace: ..
```

`workspace: ..` means sibling clones under `~/Workspace/handson/diet_coke/`.

---

## Phase 4 — Secrets and doctor

```bash
cd ~/Workspace/handson/diet_coke/diet_coke-meta
cp .env.example .env
# Edit .env — paste fine-grained PAT (never commit)

export LAUNCHPAD_TENANT_ROOT="$(pwd)"
launchpad whoami
launchpad doctor
```

---

## Phase 5 — Factory bootstrap (automated with PAT)

Dry-run first:

```bash
launchpad setup-platform --config scripts/config/platform-kd_diet_coke.yaml --dry-run
```

Apply:

```bash
launchpad setup-platform --config scripts/config/platform-kd_diet_coke.yaml --apply
launchpad verify-platform --config scripts/config/verify-platform-kd_diet_coke.yaml
```

This runs (in order):

1. **`bootstrap-org`** — creates `diet_coke-api`, `diet_coke-bff`, `diet_coke-registry` + labels
2. **`bootstrap-teams`** — `release-managers`, `pm-team`, `backend-devs`, `frontend-devs`, …
3. **`setup-gitflow`** — `develop`, branch protection, naming ruleset (per gitflow YAML)
4. **`bootstrap-project`** — org project **Diet Coke Engineering**

**Still manual after apply:**

- Add people to teams in GitHub → Organization → Teams
- If `with_templates: true`, commit workflow PRs from local clones (`chore/setup-gitflow-enforcement`)
- Set `options.require_ci: true` in gitflow YAML and re-run `setup-gitflow --apply`

Individual steps (debug):

```bash
launchpad bootstrap-org --config scripts/config/org-kd_diet_coke.yaml --apply
launchpad bootstrap-teams --config scripts/config/org-kd_diet_coke.yaml --apply
launchpad setup-gitflow --config scripts/config/gitflow-kd_diet_coke.yaml --apply
launchpad bootstrap-project --config scripts/config/project-kd_diet_coke.yaml --apply
```

---

## Phase 6 — SDD + harness (app repos)

Clone app repos as **siblings** of `diet_coke-meta`:

```bash
cd ~/Workspace/handson/diet_coke
git clone git@github.com:kd_diet_coke/diet_coke-api.git
git clone git@github.com:kd_diet_coke/diet_coke-bff.git
git clone git@github.com:kd_diet_coke/diet_coke-registry.git
```

Sync harness (rules submodule + prayog-skills + `AGENTS.md`):

```bash
cd ~/Workspace/handson/diet_coke/diet_coke-meta
launchpad sync-harness --repo diet_coke-api --dry-run
launchpad sync-harness --repo diet_coke-api --apply
launchpad verify-harness --repo diet_coke-api
# repeat for diet_coke-bff, diet_coke-registry
```

Each app repo gets the mandatory SDD tree:

```text
docs/specification/
  product/
  as-built/
  adr/
AGENTS.md
.harness-pin.yaml
```

See [playbook/spec-layout.md](../playbook/spec-layout.md) and [playbook/sdd-workflow.md](../playbook/sdd-workflow.md).

---

## Phase 7 — First INIT (PM lane)

Work stays in **`diet_coke-meta`** (open this folder in Cursor for PM skills).

1. Draft PRD: `prd/INIT-DIET_COKE-001.md` (prayog-skills: `/prd`, `/validate-requirements`)
2. Generate manifest: `work/INIT-DIET_COKE-001.yaml` (`/generate-work-manifest`)
3. Seed board:

```bash
launchpad seed-work --config work/INIT-DIET_COKE-001.yaml --dry-run
launchpad seed-work --config work/INIT-DIET_COKE-001.yaml --apply
```

4. Dev handoff — spec PRs on app repos per [playbook/pm-dev-handoff.md](../playbook/pm-dev-handoff.md)

---

## Phase 8 — Wiki (optional)

GitHub Wiki requires the first page manually, then:

```bash
./scripts/publish-wiki   # when publish script is added to tenant
```

See [playbook/wiki-setup.md](../playbook/wiki-setup.md).

---

## Quick reference — what is automated vs manual

| Step | Automated (`launchpad` + PAT) | Manual |
|------|------------------------------|--------|
| Create GitHub org | | ✓ |
| Create & push `diet_coke-meta` | | ✓ |
| Create app repos | ✓ `bootstrap-org` | |
| Labels on repos | ✓ | |
| Teams (empty) | ✓ `bootstrap-teams` | Add members in UI |
| `develop` + protection | ✓ `setup-gitflow` | |
| Project board | ✓ `bootstrap-project` | |
| Issues from manifest | ✓ `seed-work` | Write PRD + manifest |
| Harness in app repos | ✓ `sync-harness` | Clone repos locally first |
| App code & specs | | ✓ dev PRs |
| Wiki first page | | ✓ GitHub UI |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `404` on repo during dry-run | PAT missing repo access — use **All repositories** for org |
| `seed-work` blocked | Run `verify-platform` (applied phase) first |
| Branch protection fails on private repos | Upgrade org to GitHub Team |
| `no local clone at …` for templates | Clone app repo under `workspace` path; check `options.workspace` |
| Tenant not found | `cd diet_coke-meta` or `export LAUNCHPAD_TENANT_ROOT=…` |

---

## Next

- [README.md](../README.md) — SDD + harness overview  
- [local-dev.md](local-dev.md) — test Launchpad from source  
- [multi-laptop.md](multi-laptop.md) — PAT and env per machine  
