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

Defined in `config/project-example.yaml` under `issue_types`.

| Role | GitHub Type | When |
|------|-------------|------|
| `epic` | Epic | Manifest `epic:` block |
| `task` | Task | Default for `work:` items |

**Project table:** add **Type** column; enable **Show hierarchy** for parent/child tree.

Factory PAT needs org **Issue types: Read and write**. Preflight: `launchpad verify-platform`.

---

## Automation

```bash
launchpad bootstrap-project --config config/project-example.yaml --dry-run
launchpad bootstrap-project --config config/project-example.yaml --apply
```

Or as part of platform setup:

```bash
launchpad setup-platform --apply
```

Config: `config/project-example.yaml` — columns, fields, repos.

Idempotent: safe to re-run; updates Status + single-select field options and creates missing fields.

---

## v0 codebase options

| Codebase | Repo |
|----------|------|
| `<client>-meta` | Playbook, factory, work manifests |
| `example-api` | Python pilot service |
| `example-registry` | Python backend — device/signal platform |

Extend `project-<org>.yaml` when more repos join the program board, then run:

```bash
launchpad bootstrap-project --config config/project-example.yaml --apply
```

`bootstrap-project` syncs **Status** columns and **single-select** field options (e.g. Codebase, As-built) from config.
