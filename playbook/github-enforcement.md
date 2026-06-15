# GitHub enforcement (not just documentation)

Policy docs describe intent. **These mechanisms enforce it.**

## Layers

| Layer | Enforces |
|-------|----------|
| **Teams** | Who may push to `develop` vs `main`; PM handoff — [pm-dev-handoff.md](pm-dev-handoff.md) |
| **Branch protection** | PR required, reviews, optional CI checks |
| **Ruleset** `branch-naming-standard` | Only allowed branch name patterns (blocks push) |
| **`policy-branch-name` workflow** | PRs to `develop` must use allowed prefixes + slug |
| **`policy-merge-source` workflow** | `main` accepts only `develop` (or `release/*`, `hotfix/*`) |
| **`ci` workflow** | Lint/test; required when `--require-ci` used |
| **CODEOWNERS** | Review routing per profile |
| **QA manifest** | Deploy mix (not git) — see [qa-mixed-deploy.md](qa-mixed-deploy.md) |

## Factory CLI

All bootstrap uses **`launchpad`** + `GITHUB_TOKEN`. See [python-automation.md](python-automation.md).

| Command | Purpose |
|---------|---------|
| `bootstrap-org` | Ensure repos + labels exist |
| `bootstrap-teams` | Create org teams |
| `setup-gitflow` | `develop` branch + branch protection + optional templates |
| `bootstrap-project` | Project board + fields |

All support `--dry-run` (default) and `--apply`.

## Branch protection (via API)

`setup-gitflow` uses GitHub **branch protection** API on existing repos:

- **`main`**: PR required, 1 approval, enforce admins, **push restricted to `release-managers`**
- **`develop` (app repos)**: PR required, 1 approval, enforce admins, **push restricted to profile dev team** (`backend-devs`, etc.); **`pm-team` has repo Write for handoff branches but is not in merge restrictions**
- **`develop` (<client>-meta)**: PR required, 1 approval, enforce admins, **push restricted to `pm-team`**; dev teams get **read (pull)** on meta for playbook access

Status checks are **off by default** until workflows exist. Re-run:

```bash
launchpad setup-gitflow --config scripts/config/gitflow-example-org.yaml --apply --require-ci
```

With `--require-ci`:

- **`develop`**: `ci`, `policy-branch-name`
- **`main`**: `ci`, `policy-merge-source`

### Branch naming ruleset

```bash
launchpad setup-gitflow --config scripts/config/gitflow-example-org.yaml --apply --branch-naming
```

Creates repo ruleset `branch-naming-standard` (`creation` + `update` rules; allowed prefixes excluded). Idempotent — safe to re-run.

`branch_name_pattern` alone does **not** block pushes; the ruleset must restrict creation/update on refs outside the allow list.

## Workflow: block wrong merges to main

[`templates/github/workflows/policy-merge-source.yml`](../templates/github/workflows/policy-merge-source.yml)

Required on `main` when using `--require-ci`.

## After setup

1. Add people to teams in GitHub → Organization → Teams  
2. Run `ci` on a test PR to `develop`  
3. Re-run `launchpad setup-gitflow --require-ci`  
4. Open test PR `develop` → `main`; confirm only **release-managers** can merge  
