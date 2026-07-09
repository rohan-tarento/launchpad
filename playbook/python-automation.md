# Factory automation (v0.5.10)

All **org bootstrap** runs through **one CLI**: `launchpad` + `GITHUB_TOKEN`.

Developers still use **`gh`** for day-to-day git and PRs — that is separate from the factory.

## Quick start

**Per machine (recommended):** configure once in `~/.config/launchpad/` — see [multi-laptop.md](../docs/multi-laptop.md).

```bash
launchpad clients
launchpad doctor
launchpad init-client --meta --dry-run
```

Secrets live in **`~/.config/launchpad/env.d/<slug>.env`** (not in `<slug>-meta/.env`).

**Legacy / CI:** `export GITHUB_TOKEN=...` or `LAUNCHPAD_TENANT_ROOT=...` in the shell.

---

## Create a PAT (step by step)

Use a **fine-grained PAT** scoped to your org.

### 1. Open token settings

1. Log in to GitHub as an account that can **administer** your org.
2. Click your **profile photo** (top right) → **Settings**.
3. Left sidebar → **Developer settings** (bottom).
4. **Personal access tokens** → **Fine-grained tokens**.
5. Click **Generate new token**.

### 2. Token basics

| Field | Value |
|-------|--------|
| Token name | `<slug>-meta-factory` (or similar) |
| Expiration | 90 days (or your org policy) |

### 3. Resource owner

Set to **your GitHub org** (not your personal account). This limits the token to org repos only.

### 4. Repository access

Choose **All repositories** in your org, or at minimum `<slug>-meta` and all app repos.

### 5. Repository permissions

| Permission | Access | Why |
|------------|--------|-----|
| **Administration** | Read and write | Branch protection |
| **Contents** | Read and write | Seed branches on init |
| **Metadata** | Read | Required by GitHub API |
| **Issues** | Read and write | Labels + issue templates |
| **Pull requests** | Read and write | PR templates |
| **Workflows** | Read and write | Seed CI workflows |

### 6. Organization permissions

| Permission | Access | Why |
|------------|--------|-----|
| **Administration** | Read and write | Create repos and teams |
| **Issue types** | **Read and write** | Create Epic type on project board |
| **Members** | Read and write | Team ↔ repo access grants |
| **Projects** | Read and write | Project board bootstrap |

> **Common mistake:** Issue types API fails if **Issue types** is missing or set to "No access". This is separate from **Administration**.

### 7. Generate and store

1. Click **Generate token**.
2. Copy the token once (starts with `github_pat_…`).
3. Save in your machine client registry (never commit):

```bash
mkdir -p ~/.config/launchpad/env.d
cp examples/env.d/client.env.example ~/.config/launchpad/env.d/<slug>.env
# Edit <slug>.env — paste GITHUB_TOKEN=github_pat_…
chmod 600 ~/.config/launchpad/env.d/<slug>.env
launchpad whoami
```

Also add the tenant path in `~/.config/launchpad/clients.yaml` — see [multi-laptop.md](../docs/multi-laptop.md).

| File | Committed? | Purpose |
|------|------------|---------|
| `examples/env.d/client.env.example` | Yes (in launchpad repo) | Template — copy to `~/.config/launchpad/env.d/` |
| `env.d/<slug>.env` | **No** (on your machine only) | Your real `GITHUB_TOKEN` |

Do **not** store factory tokens in `<slug>-meta/.env`. Keep a backup in your password manager.

### Classic PAT (fallback)

If fine-grained tokens are blocked by org policy, use **Classic** → **Generate new token (classic)** with:

- `repo`
- `admin:org`
- `project`
- `read:org`

Prefer fine-grained when possible.

---

## Commands (v0.5.10 — 5-command surface)

All commands default to **`--dry-run`**. Pass **`--apply`** to change GitHub or disk.

| Command | Purpose | Scope |
|---------|---------|-------|
| `onboard interview` | 4 questions → writes 5 YAMLs + registry + PAT stub | local only |
| `init-client` | Create GitHub teams, repo, gitflow, project board | `--meta` or `--repo <name>` |
| `apply-scaffold` | Run cookiecutter template into repo | `--meta` or `--repo <name>` |
| `apply-harness` | Pin constitution submodule, seed skills, write AGENTS.md | `--meta` or `--repo <name>` |
| `status` | Verify harness pins match config | `--meta` or `--repo <name>` |
| `status` | Checklist + suggest next command | `--meta` |
| `doctor` | Preflight checks (token, config, version pin) | — |
| `whoami` | Verify token and print GitHub login | — |
| `clients` | List configured programmes | — |

```bash
# Day 0 — local setup (no PAT needed)
launchpad onboard interview

# Day 1 — meta on GitHub
launchpad init-client --meta --dry-run
launchpad init-client --meta --apply

# Day 1 — scaffold + harness meta
launchpad apply-scaffold --meta --apply
launchpad apply-harness --meta --apply
launchpad status --meta

# Day N — app repos (repeat per repo)
launchpad init-client --repo example-api --apply
launchpad apply-scaffold --repo example-api --apply
launchpad apply-harness --repo example-api --apply
launchpad status --repo example-api

```

### YAML kinds (`config/`)

| File | Schema kind | Used by |
|------|-------------|---------|
| `programme.yaml` | `Programme` | `init-client`, `doctor`, all commands |
| `governance-{org}.yaml` | `GovernanceConfig` | `init-client` — teams, repos, stacks, board |
| `harness-{org}.yaml` | `HarnessConfig` | `apply-harness`, `status` |
| `scaffold-{org}.yaml` | `ScaffoldConfig` | `apply-scaffold` |
| `service-catalog-{org}.yaml` | `ServiceCatalog` | `status`, `status` |

Backlog: `work/*.yaml` with `kind: WorkManifest` — documentation format for multi-repo bulk seeding; v0.5.10 has no `seed-work` CLI (use `gh issue create` per wave).

Harness commands (no GitHub API required, work without PAT):

```bash
launchpad apply-harness --repo example-api --dry-run
launchpad apply-harness --repo example-api --apply
launchpad status --repo example-api
```

See [harness-pins.md](harness-pins.md).

Help: `launchpad --help` or `launchpad init-client --help`.

---

## What stays manual

- Add people to teams (GitHub UI)
- Push `<slug>-meta` to `main` after scaffolding
- Open / merge workflow PRs after templates are seeded

---

## Package layout

```
launchpad/                  ← CLI package
  commands/                 ← 5-command implementations
  forge/                    ← GitHub ForgeProvider
  onboarding/               ← interview flow
  schema/                   ← 5-YAML validators
examples/tenant-meta/       ← tenant skeleton (example-org)
playbook/                   ← process SSOT
docs/                       ← schema, greenfield guide, stacks
```
