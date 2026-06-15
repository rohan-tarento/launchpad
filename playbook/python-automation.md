# Python factory automation (PAT)

All **org bootstrap** runs through **one CLI**: Python + `GITHUB_TOKEN`.

Developers still use **`gh`** for day-to-day git and PRs — that is separate from the factory.

## Quick start

```bash
cd <client>-meta
cp .env.example .env
# Edit .env — paste your PAT (file is gitignored; never commit)
launchpad whoami
launchpad verify-platform
launchpad setup-platform --dry-run
```

`launchpad` loads **`<client>-meta/.env`** automatically and creates `scripts/py/.venv` on first run.

You can still `export GITHUB_TOKEN=...` in the shell; that overrides `.env` if both are set.

---

## Create a PAT (step by step)

Use a **fine-grained PAT** scoped to **example-org**.

### 1. Open token settings

1. Log in to GitHub as an account that can **administer** `example-org`.
2. Click your **profile photo** (top right) → **Settings**.
3. Left sidebar → **Developer settings** (bottom).
4. **Personal access tokens** → **Fine-grained tokens**.
5. Click **Generate new token**.

### 2. Token basics

| Field | Value |
|-------|--------|
| Token name | `<client>-meta-factory` (or similar) |
| Expiration | 90 days (or your org policy) |
| Description | Optional — e.g. “<client>-meta factory bootstrap” |

### 3. Resource owner

| Field | Value |
|-------|--------|
| Resource owner | **`example-org`** (the org — not your personal account) |

This limits the token to example-org repos only.

### 4. Repository access

Choose **All repositories** in `example-org`, or select at least **<client>-meta** and **example-api**.

### 5. Repository permissions

| Permission | Access | Why |
|------------|--------|-----|
| **Administration** | Read and write | Branch protection, rulesets |
| **Contents** | Read and write | `options.init_empty: true` in gitflow YAML |
| **Metadata** | Read | Required by GitHub API |
| **Issues** | Read and write | Create labels |

### 6. Organization permissions

| Permission | Access | Why |
|------------|--------|-----|
| **Administration** | Read and write | Create repos and teams |
| **Issue types** | **Read and write** | **Required** — `verify-factory`, create **Epic** type, `seed-work` |
| **Members** | Read and write | Team ↔ repo access grants |
| **Projects** | Read and write | Project board bootstrap |

> **Common mistake:** `verify-factory` fails on Issue types API if **Issue types** is missing or set to “No access”. That is separate from **Administration**.

#### Edit an existing factory token

1. GitHub → **Settings** → **Developer settings** → **Fine-grained tokens**
2. Open `<client>-meta-factory` (or your token name)
3. Scroll to **Organization permissions** → **example-org**
4. Set **Issue types** → **Read and write**
5. **Update token** → copy new value into `<client>-meta/.env` → `launchpad verify-factory`

### 7. Generate and store in `.env`

1. Click **Generate token**.
2. Copy the token **once** (starts with `github_pat_…`).
3. Save it in the project env file (gitignored):

```bash
cd <client>-meta
cp .env.example .env
# Open .env and replace github_pat_REPLACE_ME with your real token
launchpad whoami
```

| File | Committed? | Purpose |
|------|------------|---------|
| `.env.example` | Yes | Template — no secrets |
| `.env` | **No** (in `.gitignore`) | Your real `GITHUB_TOKEN` |

Keep a backup in your password manager. Do not commit `.env` or paste the token in chat/PRs.

### Classic PAT (fallback)

If fine-grained tokens are blocked by org policy, use **Classic** → **Generate new token (classic)** with:

- `repo`
- `admin:org`
- `project`
- `read:org`

Scope the classic token to **example-org** only; prefer fine-grained when possible.

---

## Commands

All commands default to **`--dry-run`**. Pass **`--apply`** to change GitHub.

| Command | Purpose |
|---------|---------|
| `whoami` | Verify token and print GitHub login |
| `setup-platform` | **Platform baseline** from `PlatformManifest` YAML |
| `verify-platform` | **Ready for backlog?** from `VerifyManifest` YAML |
| `verify-factory` | Alias for `verify-platform` |
| `bootstrap-org` | Repos + labels (`org-*.yaml`) |
| `bootstrap-teams` | Teams (`org-*.yaml`) |
| `setup-gitflow` | `develop`, protection (`gitflow-*.yaml`) |
| `bootstrap-project` | Board + fields + issue types (`project-*.yaml`) |
| `seed-work` | Backlog from `WorkManifest` (`work/*.yaml`) |
| `seed-issues` | Alias for `seed-work` |
| `sync-harness` | Pin rules submodule, seed prayog-skills dev bundle, `.harness-pin.yaml`, `AGENTS.md` |
| `verify-harness` | Check harness pins and submodules in app repos |

```bash
# After cp .env.example .env and pasting your PAT:

# Platform (repos + teams + gitflow + board + verify)
launchpad setup-platform \
  --config scripts/config/platform-example-org.yaml \
  --dry-run
launchpad setup-platform \
  --config scripts/config/platform-example-org.yaml \
  --apply

launchpad verify-platform \
  --config scripts/config/verify-platform-example-org.yaml

# Backlog (WorkManifest per initiative — generate via /generate-work-manifest)
launchpad seed-work --config work/INIT-<id>.yaml --dry-run
launchpad seed-work --config work/INIT-<id>.yaml --apply

# Individual steps (debug / partial re-run)
launchpad bootstrap-org --config scripts/config/org-example-org.yaml --apply
launchpad bootstrap-teams --config scripts/config/org-example-org.yaml --apply
launchpad setup-gitflow --config scripts/config/gitflow-example.yaml --apply
launchpad bootstrap-project --config scripts/config/project-example-org.yaml --apply
```

### YAML kinds (`scripts/config/`)

| File | `kind` | Used by |
|------|--------|---------|
| `org-{org}.yaml` | `OrgConfig` | `bootstrap-org`, `bootstrap-teams` |
| `gitflow-{org}.yaml` | `GitflowConfig` | `setup-gitflow` — **authoritative** for branch naming, merge policy, PR rules, CI gates |
| `project-{org}.yaml` | `ProjectConfig` | `bootstrap-project`, `seed-work` (fields) |
| `platform-{org}.yaml` | `PlatformManifest` | `setup-platform` |
| `verify-platform-{org}.yaml` | `VerifyManifest` | `verify-platform` |
| `harness-{org}.yaml` | `HarnessConfig` | `sync-harness`, `verify-harness` |

Backlog: `work/*.yaml` with `kind: WorkManifest` — **not** in platform YAML.

Harness (no GitHub API — works without PAT):

```bash
launchpad sync-harness --repo example-api --dry-run
launchpad sync-harness --repo example-api --apply
launchpad verify-harness --repo example-api
```

See [harness-pins.md](harness-pins.md).

`seed-work --apply` requires `verify-platform` (applied) to pass.

Help: `launchpad --help` or `launchpad setup-platform --help`.

Do **not** set `options.init_empty: true` on repos that already have history.

---

## What stays manual

- Add people to teams (GitHub UI)
- Push **<client>-meta** to `main`
- Open / merge workflow PRs (`options.with_templates: true` copies files to local clones)
- Set `options.require_ci: true` in gitflow YAML after workflows exist, then re-run `setup-gitflow --apply`

---

## Package layout

```
scripts/meta                ← only entry point you need
scripts/py/meta_scripts/    ← Python implementation
scripts/py/requirements.txt
scripts/config/*.yaml
```
