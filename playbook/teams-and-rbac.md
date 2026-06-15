# Teams and RBAC (example-org)

Config: [`gitflow-example.yaml`](../examples/tenant-meta/scripts/config/gitflow-example.yaml)

**PM ↔ dev handoff:** [pm-dev-handoff.md](pm-dev-handoff.md)

## Teams

| Team slug | Role |
|-----------|------|
| `pm-team` | **Product** — PRD and meta `develop` merges; **Write** on app repos for spec handoff PRs (does **not** merge app `develop`) |
| `release-managers` | **Only** group allowed to **merge/push to `main`** (release line) |
| `backend-devs` | Python microservices — merge to **`develop`** on backend repos |
| `frontend-devs` | Ops portal / BFF — merge to **`develop`** on frontend repos |
| `platform-devs` | Compose, shared workflows — merge to **`develop`** on platform app repos (not meta) |
| `data-platform-devs` | Manthan / data pipeline (add when those repos join the model) |

Optional: nest all dev teams under parent team `engineers` for @mentions (not used for `main`).

## Access matrix (example-org v0)

| Repo | `pm-team` | Dev teams | `develop` merge |
|------|-----------|-------------|-----------------|
| **<client>-meta** | **Write** | **Read** (pull) — playbook access | **`pm-team`** |
| **example-api** | Write (handoff branches) | `backend-devs` Write | `backend-devs` |
| **all — `main`** | — | — | **`release-managers` only** |

PM pushes spec handoff branches on app repos; **dev merges** after review. PM merges meta playbook PRs on **<client>-meta**.

## Repo → team mapping (develop merge)

| Profile | v0 repos (example-org) | Future repos |
|---------|----------------------|--------------|
| `backend` | **example-api** | example-registry, setu, kavach, pravah, airforge |
| `frontend` | — | example-bff |
| `platform` | **<client>-meta** | iac, iac-local |
| `data_platform` | — | example-platform, pramana |

Config file: [`examples/tenant-meta/scripts/config/gitflow-example.yaml`](../examples/tenant-meta/scripts/config/gitflow-example.yaml)

## Branch rules (summary)

| Branch | PR required | Reviews | Who can merge to branch |
|--------|-------------|---------|-------------------------|
| `chore/*`, `feature/*` | → `develop` via PR | ≥1 | Profile team (app) or `pm-team` (meta) |
| `develop` | Yes | ≥1 | Profile team / `pm-team` (per repo) |
| `main` | Yes, from `develop` only | ≥1 (+ release for promote PR) | **`release-managers` only** |

See [github-enforcement.md](github-enforcement.md) and [branching-policy.md](branching-policy.md).

## Automation

Requires `GITHUB_TOKEN` — [python-automation.md](python-automation.md).

```bash
# cp .env.example .env — paste PAT (see python-automation.md)

launchpad setup-platform --config scripts/config/platform-example-org.yaml --apply
# or individual steps:
launchpad bootstrap-teams --config scripts/config/org-example-org.yaml --apply
launchpad setup-gitflow --config scripts/config/gitflow-example.yaml --apply
```

Add members to **`pm-team`** and dev teams in GitHub UI after team creation.
