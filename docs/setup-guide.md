# Setup guide

End-to-end onboarding using the **single** tenant skeleton: [`examples/tenant-meta/`](../examples/tenant-meta/).

Launchpad (the kit) and `<client>-meta` (the tenant) are **separate repos**. Install Launchpad once; copy `tenant-meta` per client.

---

## Architecture

```text
~/Workspace/handson/
├── launchpad/              # public kit — CLI, playbook, templates (clone once)
└── <client>/               # e.g. diet_coke/
    ├── <client>-meta/      # private tenant — copy from examples/tenant-meta/
    ├── <app-api>/          # app repos (siblings, created by factory or manual)
    └── <app-bff>/
```

| Repo | Role |
|------|------|
| **launchpad** | Factory CLI + playbook — **not** copied into meta |
| **`<client>-meta`** | PRDs, `work/`, factory YAML, wiki source |
| **App repos** | Specs, code, harness pin |

---

## Naming example (illustrative only)

When you onboard a real client, you choose names — there is **no second example folder** in this repo.

| You choose | Example |
|------------|---------|
| GitHub org | `kd_diet_coke` |
| Project slug | `diet_coke` |
| Meta repo | `diet_coke-meta` |
| App repos | `diet_coke-api`, `diet_coke-bff` |

The skeleton ships with neutral **`example-org`** / **`example-api`** so smoke tests work without renaming. For production, search-replace in YAML and rename config files to `*-kd_diet_coke.yaml`.

---

## Phase 0 — Prerequisites (manual)

1. **GitHub org** exists (org admin access).
2. **GitHub Team** plan for branch protection on private repos (if needed).
3. **Private rules repo** with `.mdc` constitution (harness submodule).
4. **Fine-grained PAT** — [playbook/bootstrap-prerequisites.md](../playbook/bootstrap-prerequisites.md).

`gh auth login` is for day-to-day PRs. Factory uses **`GITHUB_TOKEN`** in `~/.config/launchpad/env.d/<client-id>.env`.

---

## Phase 1 — Install Launchpad (once per machine)

**Operators (recommended):**

```bash
git clone https://github.com/drivestream-lab/launchpad.git ~/Workspace/handson/launchpad
cd ~/Workspace/handson/launchpad
pipx install -e .
launchpad --help
```

**Kit contributors** (optional): [local-dev.md](local-dev.md) — venv + `./bin/launchpad`.

---

## Phase 2 — Create tenant meta

```bash
mkdir -p ~/Workspace/handson/diet_coke
cp -r ~/Workspace/handson/launchpad/examples/tenant-meta \
      ~/Workspace/handson/diet_coke/diet_coke-meta
cd ~/Workspace/handson/diet_coke/diet_coke-meta
git init
git remote add origin git@github.com:kd_diet_coke/diet_coke-meta.git
```

Create **`diet_coke-meta`** on GitHub first, then push. Meta is **not** created by `bootstrap-org`.

**Customize configs** — edit `scripts/config/*.yaml`:

- Replace `example-org` → `kd_diet_coke`
- Replace `example-api` → `diet_coke-api` (and other repos)
- Rename files: `org-example.yaml` → `org-kd_diet_coke.yaml`, etc.
- Update `platform-*.yaml` step `config:` paths to match new filenames

Or keep `example-org` names for a sandbox org while learning.

---

## Phase 3 — Client registry and doctor

One-time per machine — [multi-laptop.md](multi-laptop.md):

```bash
mkdir -p ~/.config/launchpad/env.d
cp ~/Workspace/handson/launchpad/examples/clients.yaml.example ~/.config/launchpad/clients.yaml
cp ~/Workspace/handson/launchpad/examples/env.d/client.env.example \
   ~/.config/launchpad/env.d/diet_coke.env
# Edit clients.yaml (path to diet_coke-meta) and diet_coke.env (GITHUB_TOKEN)
chmod 600 ~/.config/launchpad/env.d/diet_coke.env

launchpad --client diet_coke doctor
```

Or set `default: diet_coke` in `clients.yaml` and run `launchpad doctor`.

---

## Phase 4 — Factory bootstrap (PAT required)

```bash
launchpad setup-platform --config scripts/config/platform-<org>.yaml --dry-run
launchpad setup-platform --config scripts/config/platform-<org>.yaml --apply
launchpad verify-platform --config scripts/config/verify-platform-<org>.yaml
```

Runs: `bootstrap-org` → `bootstrap-teams` → `setup-gitflow` → `bootstrap-project`.

Gitflow policy is **only** in `gitflow-<org>.yaml` — no CLI policy flags.

**Manual after apply:** add team members; merge workflow PRs if `options.with_templates: true`; then set `options.require_ci: true` and re-run `setup-gitflow --apply`.

---

## Phase 5 — Harness (app repos)

Clone app repos as siblings of meta, then:

```bash
launchpad sync-harness --repo diet_coke-api --apply
launchpad verify-harness --repo diet_coke-api
```

See [playbook/harness-pins.md](../playbook/harness-pins.md) and [playbook/sdd-workflow.md](../playbook/sdd-workflow.md).

---

## Phase 6 — First INIT

In **`<client>-meta`** (PM lane):

1. `prd/INIT-….md`
2. `work/INIT-….yaml` (e.g. sample `work/INIT-EXAMPLE-001.yaml` in skeleton)
3. `launchpad seed-work --config work/INIT-….yaml --apply`

---

## Automated vs manual

| Step | Launchpad + PAT | Manual |
|------|-----------------|--------|
| Create org | | ✓ |
| Create & push `<client>-meta` | | ✓ |
| Create app repos | ✓ `bootstrap-org` | |
| Teams, gitflow, board | ✓ `setup-platform` | Add people in UI |
| Issues | ✓ `seed-work` | PRD + manifest |
| Harness | ✓ `sync-harness` | Clone repos first |

---

## Docs

- [new-client.md](new-client.md) — checklist  
- [multi-laptop.md](multi-laptop.md) — install + client registry  
- [local-dev.md](local-dev.md) — kit contributors / source testing  
- [SCHEMA.md](SCHEMA.md) — `launchpad/v1` YAML kinds  
