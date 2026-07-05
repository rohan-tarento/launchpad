# GitHub enforcement (not just documentation)

Policy docs describe intent. **These mechanisms enforce it.**

**Single source of truth:** `config/gitflow-<org>.yaml` (`kind: GitflowConfig`). Branch naming, merge policy, PR rules, CI gates, and automation switches live there — **not** on the CLI.

## Layers

| Layer | Enforces |
|-------|----------|
| **Teams** | Who may push to `develop` vs `main`; merge rules — [delivery-workflow.md](delivery-workflow.md) |
| **Branch protection** | PR required, reviews (`protection` in gitflow YAML) |
| **Ruleset** `branch-naming-standard` | Only allowed branch name patterns (when `options.branch_naming: true`) |
| **`policy-branch-name` workflow** | PRs to `develop` — generated from `branch_naming` + `merge_policy.develop` |
| **`policy-merge-source` workflow** | `main` accepts only allowed sources — generated from `merge_policy.main` |
| **`ci` workflow** | Lint/test; required when `options.require_ci: true` |
| **CODEOWNERS** | Review routing per profile |
| **QA manifest** | Deploy mix (not git) — documented in tenant `qa/` directory per org (not in launchpad kit) |

## Factory CLI

All bootstrap uses **`launchpad`** + `GITHUB_TOKEN`. See [python-automation.md](python-automation.md).

| Command | Purpose |
|---------|---------|
| `bootstrap-org` | Ensure repos + labels exist (OrgConfig + gitflow union, includes meta) |
| `bootstrap-teams` | Create org teams |
| `seed-repos` | Seed `main`, create `develop`, set default branch `develop` |
| `setup-gitflow` | Reconcile GitHub to `gitflow-*.yaml` |
| `bootstrap-project` | Project board + fields |

```bash
launchpad seed-repos --config config/gitflow-<org>.yaml --apply
launchpad setup-gitflow --config config/gitflow-<org>.yaml --apply
```

Only `--config`, `--apply` / `--dry-run`, `--org`, and `--repo` (debug filter) are valid. Policy is never passed on the command line.

## Gitflow YAML sections

| Section | Controls |
|---------|----------|
| `teams` / `repos` | Who merges `develop` per repo; `main` → `release-managers` |
| `options.require_ci` | Require `ci`, `policy-branch-name` (develop), `policy-merge-source` (main) |
| `options.branch_naming` | Create `branch-naming-standard` ruleset |
| `options.with_templates` | Copy workflows + CODEOWNERS into local clones under `options.workspace` |
| `options.seed_empty` | Seed empty repos on `main` during `seed-repos` (default: true) |
| `options.init_empty` | Deprecated alias for `seed_empty` |
| `branch_naming` | Prefixes, `mode` (standard/strict), exceptions |
| `protection` | Review count, stale dismiss, enforce admins per branch |
| `merge_policy` | Allowed PR sources to `develop` / `main` (workflow content) |

## Branch protection (via API)

`setup-gitflow` uses GitHub **branch protection** API on existing repos:

- **`main`**: PR required, reviews from `protection.main`, **push restricted to `release-managers`**
- **`develop` (app repos)**: PR required, **push restricted to profile dev team**; **`pm-team` has Write for handoff branches but is not in merge restrictions**
- **`develop` (<client>-meta)**: **push restricted to `pm-team`**; dev teams get **read (pull)** on meta

When `options.require_ci: true` (after workflow PRs are merged):

- **`develop`**: `ci`, `policy-branch-name`
- **`main`**: `ci`, `policy-merge-source`

Typical rollout in gitflow YAML:

1. Bootstrap with `require_ci: false`, `with_templates: true` — merge workflow PRs
2. Set `require_ci: true` — re-run `setup-gitflow --apply`

### Branch naming ruleset

Set `options.branch_naming: true` in gitflow YAML. Creates repo ruleset `branch-naming-standard` using `branch_naming.allowed_prefixes` and `exceptions`. Idempotent — safe to re-run.

## Workflow templates

When `options.with_templates: true`, Launchpad generates `policy-branch-name.yml` and `policy-merge-source.yml` from gitflow YAML (not hand-edited). Base reference: [`templates/github/workflows/`](../templates/github/workflows/).

## After setup

1. Add people to teams in GitHub → Organization → Teams  
2. Run `ci` on a test PR to `develop`  
3. Set `options.require_ci: true` in gitflow YAML and re-run `setup-gitflow --apply`  
4. Open test PR `develop` → `main`; confirm only **release-managers** can merge  
