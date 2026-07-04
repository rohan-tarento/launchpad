# Branching policy

Applies to **example-org** repositories in the factory config.

## Branches

| Branch | Purpose |
|--------|---------|
| `main` | Release line — **stage / prod** images; only **release-managers** merge |
| `develop` | Integration line — **QA baseline**; dev teams merge feature PRs here |
| `feature/<initiative>-<slug>` | Work branches; PR target = **`develop`** |
| `fix/<slug>` or `hotfix/<slug>` | Prod fix from `main`; backport to `develop` |
| `release/<version>` | Optional release freeze (later) |
| `chore/<slug>` | Tooling, bootstrap, repo hygiene (no product code) |

We do **not** use long-lived per-customer branches.

## Branch naming (enforced)

Random branch names (`my-test`, `john-fix`, `tmp`) are **not** allowed.

### Allowed prefixes

| Prefix | Target PR | Example |
|--------|-----------|---------|
| `feature/` | `develop` | `feature/INIT-EXAMPLE-002-w1-jwt-login` |
| `fix/` | `develop` (or `main` for prod fix flow) | `fix/registry-404-mapping` |
| `hotfix/` | `main` (then backport to `develop`) | `hotfix/compose-image-pin` |
| `release/` | `main` (optional) | `release/2026.06.0` |
| `chore/` | `develop` | `chore/setup-gitflow-enforcement` |

**Protected long-lived:** `main`, `develop` — never used as feature branch names.

**Automation exceptions:** `dependabot/*` (allowed via ruleset; not for humans).

### Slug rules

- **Letters, digits**, `.`, `_`, `-` only (initiative ids use standard casing: `BOOTSTRAP-001`, `INIT-…`)  
- Must be at least one character after `/`  
- Use **kebab-case** after the initiative segment where possible

### Initiative segment

All product INIT branches use `INIT-{COMPONENT}-{NUMBER}` as the canonical identity segment:

| Placeholder | Meaning | Example |
|-------------|---------|---------|
| `COMPONENT` | Service `branch_code` from `service-catalog.yaml` — 2–7 uppercase chars | `MOBBOT`, `KAVACH`, `MNTHAN` |
| `NUMBER` | Initiative sequence number — 1–7 digits | `001`, `0012` |

This segment is set once when the PRD is created and never changed. It is used verbatim in every branch — no abbreviation or short-code registration required.

### Strict vs standard

| Mode | When | `feature/*` rule |
|------|------|------------------|
| **standard** | Bootstrap / chore-heavy work | `feature/<any-valid-slug>` |
| **strict** | Product INIT (recommended) | `feature/INIT-{COMPONENT}-{NUMBER}-w{N}-{slug}` |

Switch to `strict` in `gitflow-{org}.yaml` when the org begins product INIT delivery.

### Spec pipeline branches (chore/)

The spec pipeline produces docs-only artifacts before implementation starts.
These use `chore/` — no product code, safe to merge without QA phase.

| Artifact | Branch |
|----------|--------|
| Technical Design Document | `chore/INIT-{COMPONENT}-{NUMBER}-technical-review` |
| Implementation plan | `chore/INIT-{COMPONENT}-{NUMBER}-plan` |

Note: the feasibility report lives on the **prd-handoff branch** alongside the spec slice — no separate chore branch.

### Wave pipeline branches (feature/)

One branch per wave following the 1:1 rule (see `delivery-model.md`).
The ground report and as-built update are the last commits on the feature
branch — committed before the PR is marked ready for review.

| Wave | Branch | Contains |
|------|--------|----------|
| W0 | `feature/INIT-{COMPONENT}-{NUMBER}-w0-{slug}` | W0 code + ground report + as-built |
| W1 | `feature/INIT-{COMPONENT}-{NUMBER}-w1-{slug}` | W1 code + ground report + as-built |
| W{N} | `feature/INIT-{COMPONENT}-{NUMBER}-w{N}-{slug}` | W{N} code + ground report + as-built |

### What we block

| Bad example | Why |
|-------------|-----|
| `random-branch` | Missing required prefix |
| `feature/` | Empty slug |
| `Feature/foo` | Wrong case |
| `feature/foo bar` | Spaces |
| `develop` as PR source | Must not PR from long-lived branches |

### Enforcement layers

| Layer | Blocks | Script |
|-------|--------|--------|
| **Ruleset** `branch-naming-standard` | Push/create of badly named branches (`creation` + `update`) | `options.branch_naming: true` in gitflow YAML |
| **Workflow** `policy-branch-name` | PR to `develop` with bad head ref | `options.with_templates` + `options.require_ci` in gitflow YAML |
| **Workflow** `policy-merge-source` | PR to `main` not from `develop` / `release/*` / `hotfix/*` | already deployed |

Docs alone are not enough — use ruleset + workflows together.

## Flow

```text
feature/* ──PR (review)──► develop ──QA phase A/B──► PR ──► main ──► stage / prod
                              ▲                           │
                              └── hotfix backport ──────────┘
```

## QA (cross-repo)

- **Phase A:** QA deploy = `develop` images + **manifest override** for feature PR image(s)  
- **Phase B:** All repos on `develop` — repeat sanity  
- **Release:** `release-managers` merge `develop` → `main`  

Manifests: add per-initiative `qa/manifests/<init>.yaml` files in your tenant meta repo (not in launchpad kit).

## Enforcement

See [github-enforcement.md](github-enforcement.md) and [teams-and-rbac.md](teams-and-rbac.md).
