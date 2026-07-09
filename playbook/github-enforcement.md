# GitHub enforcement (not just documentation)

Policy docs describe intent. **These mechanisms enforce it.**

**Single source of truth (v0.5.10):** `config/governance-<org>.yaml` (`kind: GovernanceConfig`). Teams, repos, branch policy (`policy:` block), and project board live there — **not** on the CLI.

---

## What `init-client` automates today

| Step | Action |
|------|--------|
| Teams | Create teams from `teams:` block |
| Repos | Create repos from `repos:` block |
| Access | Grant repo teams from each repo's `teams:` list |
| Gitflow | Set `policy.default_branch`; create `policy.integration_branch` (default `develop`); apply PR review protection on both |
| Board | Create org project (`project_board:`) and link repos |

```bash
launchpad init-client --meta --dry-run      # preview Day 1
launchpad init-client --meta --apply
launchpad init-client --repo <name> --apply # Day N per app repo
```

Config is resolved from `--client <id>` → `clients.yaml` → `config/` (no `--config` flag).

### Policy fields (`governance-<org>.yaml`)

```yaml
policy:
  default_branch: main
  integration_branch: develop   # feature PR target; created from main if absent
  require_pr_reviews: 1
  dismiss_stale_reviews: true
```

Edit policy in YAML, PR to meta, re-run `init-client --apply` — idempotent.

---

## Advanced enforcement (manual / reference templates)

v0.5.10 does **not** yet automate rulesets or workflow seeding. Tenants deploy workflow reference templates from [`launchpad/templates/github/workflows/`](../launchpad/templates/github/workflows/):

| Template | Purpose |
|----------|---------|
| `policy-branch-name.yml` | Validates branch names on PRs to `develop` |
| `policy-merge-source.yml` | Restricts merge sources into `main` |
| `ci.yml` | Lint/test gate |

Copy into each repo's `.github/workflows/`, tune for your org, and enable as required checks when ready. See [branching-policy.md](branching-policy.md) for naming rules and rollout phases.

---

## Enforcement layers (target state)

| Layer | Enforces |
|-------|----------|
| **Teams** | Who may push to `develop` vs `main`; merge rules — [delivery-workflow.md](delivery-workflow.md) |
| **Branch protection** | PR required, reviews (`policy` in governance YAML) |
| **Ruleset** `branch-naming-standard` | Allowed branch name patterns (manual deploy) |
| **`policy-branch-name` workflow** | PRs to `develop` — head ref validation |
| **`policy-merge-source` workflow** | `main` accepts only allowed sources |
| **`ci` workflow** | Lint/test; required check when enabled |
| **CODEOWNERS** | Review routing per profile |
| **QA manifest** | Deploy mix (not git) — documented in tenant `qa/` directory per org (not in launchpad kit) |

---

## Branch protection (via API)

`init-client` uses GitHub **branch protection** API on the default branch:

- PR required
- Reviews from `policy.require_pr_reviews` (default: 1)
- Stale review dismissal from `policy.dismiss_stale_reviews` (default: true)

**GitHub Team plan** is required for branch protection on private repos. See [bootstrap-prerequisites.md](bootstrap-prerequisites.md).

### Typical rollout

1. Bootstrap with `init-client --apply` — default branch + basic protection
2. Merge workflow PRs (policy-branch-name, policy-merge-source, ci) into each repo
3. Enable those workflows as required checks in branch protection (GitHub UI or API)

---

## After setup

1. Add people to teams in GitHub → Organization → Teams
2. Run `ci` on a test PR to `develop`
3. Enable workflow required checks when workflows are merged
4. Open test PR `develop` → `main`; confirm **release-managers** can merge

See [teams-and-rbac.md](teams-and-rbac.md) and [python-automation.md](python-automation.md).
