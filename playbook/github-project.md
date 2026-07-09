# GitHub Project — engineering board (required)

Org-level project for sprint tracking on **example-org**.

Playbook SSOT stays in **<client>-meta**; the project is for **work items** (issues/PRs).

**Live board:** [Example Engineering](https://github.com/orgs/example-org/projects/1)

---

## Columns (Status field — workflow only)

Fixed order — **7 columns, not optional:**

| # | Column | When |
|---|--------|------|
| 1 | Backlog | Captured, not triaged |
| 2 | Spec/CR | Spec gap, CR draft, cross-service review |
| 3 | Ready | Approved to start; all required fields set |
| 4 | In progress | `feature/INIT-{COMPONENT}-{NUMBER}-w{N}-*` (see branching-policy.md) or `chore/…` branch active |
| 5 | Verify | Live verify run |
| 6 | In review | PR open to `develop` |
| 7 | Done | Merged to `develop` or closed |

---

## Custom fields (required on every item)

| Field | Type | Example |
|-------|------|---------|
| Initiative | Text | `BOOTSTRAP-001` |
| CR | Text | `CR-001` or `N/A` |
| Codebase | Single select | `example-api` or `<client>-meta` |
| Spec path | Text | `docs/specification/product/02-api-contract.md` |
| Verify command | Text | `make check` |
| As-built | Single select | `yes` / `no` / `N/A` |
| QA manifest | Text | `N/A` (or path when QA manifests exist) |

Fill **Initiative, CR, Codebase, Spec path** before leaving **Ready**.  
Fill **Verify command** before leaving **Verify**.  
Set **As-built** before **In review**.

---

## Labels (repos — use with fields)

| Label | Use |
|-------|-----|
| `initiative` | Epic / INIT |
| `bootstrap` | Platform bootstrap (BOOTSTRAP-001) |
| `cr` | Cross-service CR |
| `repo:example-api` / `repo:meta` | Matches **Codebase** field |
| `spec` | Spec/CR column work |
| `verify` | Verify column work |

---

## Issue types (org — color on board)

Configure in GitHub org settings (factory PAT needs org **Issue types: Read and write**).

| Role | GitHub Type | When |
|------|-------------|------|
| `epic` | Epic or **Feature** (org-specific) | Parent initiative |
| `task` | Task | Default for wave work items |

Set your org's parent/initiative type name (e.g. some enterprises use **Feature**, not Epic).

**Project table:** add **Type** column; enable **Show hierarchy** for parent/child tree.

Preflight: `launchpad status --meta`.

---

## Automation (v0.5.10)

`init-client` creates the org project board (when `project_board.enabled: true` in `governance-<org>.yaml`) and links each repo:

```bash
launchpad init-client --meta --dry-run
launchpad init-client --meta --apply
```

Config: `config/governance-<org>.yaml` — `project_board.name`, `project_board.enabled`.

**Manual setup (today):** Status columns, custom fields, single-select options, issue types, and team board access are configured in the GitHub Projects UI after the board exists. v0.5.10 does not sync column/field definitions from YAML.

### Team access (board visibility)

Repo team grants (`init-client`) do **not** grant access to the org project board. Add teams as project collaborators in GitHub → Project → Settings → Manage access. Roles: `READER`, `WRITER`, `ADMIN`.

---

## v0 codebase options

| Codebase | Repo |
|----------|------|
| `<client>-meta` | Playbook, factory, work manifests |
| `example-api` | Python pilot service |
| `example-registry` | Python backend — device/signal platform |

Add repos to `governance-<org>.yaml`, then run `launchpad init-client --repo <name> --apply` to link new repos to the board.
