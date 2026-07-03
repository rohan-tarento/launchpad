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
| `feature/` | `develop` | `feature/INIT-EXAMPLE-002-example-api-jwt` |
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
- **Max readable length:** keep branch names under ~50 characters — see short-code rule below

### Short-code rule

Initiative IDs longer than **12 characters** must register a `short_code` in the
WorkManifest before the first branch is created. Use the short-code in all branch
names — never the full initiative ID.

| Full initiative ID | Short-code | Example branch |
|-------------------|------------|----------------|
| `INIT-MANTHAN-PLATFORM-T1-001` | `MNT-T1-001` | `feature/MNT-T1-001-w1-extraction` |
| `INIT-KOLA-REGISTRY-002` | `KOL-002` | `feature/KOL-002-w2-storage` |
| `PRD-001` | `PRD-001` (already short) | `feature/PRD-001-w1-extraction` |

**Format:** `{AREA-ABBREV}-{NNN}` — 3–4 letter area prefix + initiative number.
**Uniqueness:** short-codes must be unique per org.
**Registration:** declare in WorkManifest `short_code:` field — set once, never change after first branch is created.

### Strict vs standard

| Mode | When | `feature/*` rule |
|------|------|------------------|
| **standard** | Bootstrap / chore-heavy work | `feature/<any-valid-slug>` |
| **strict** | Product INIT (recommended) | `feature/{sc}-w{N}-{slug}` where `{sc}` = short-code |

### Spec pipeline branches (chore/)

The spec pipeline produces docs-only artifacts before implementation starts.
These use `chore/` — no product code, safe to merge without QA phase.

| Artifact | Branch |
|----------|--------|
| Feasibility report | `chore/{sc}-feasibility` |
| Technical Design Document | `chore/{sc}-technical-review` |
| Implementation plan | `chore/{sc}-plan` |

### Wave pipeline branches (feature/)

One branch per wave following the 1:1 rule (see `delivery-model.md`).
The ground report and as-built update are the last commits on the feature
branch — committed before the PR is marked ready for review.

| Wave | Branch | Contains |
|------|--------|----------|
| W0 | `feature/{sc}-w0-{slug}` | W0 code + ground report + as-built |
| W1 | `feature/{sc}-w1-{slug}` | W1 code + ground report + as-built |
| W{N} | `feature/{sc}-w{N}-{slug}` | W{N} code + ground report + as-built |

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
