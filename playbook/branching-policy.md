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

### Strict vs standard

| Mode | When | `feature/*` rule |
|------|------|------------------|
| **standard** | Bootstrap / chore-heavy work | `feature/<any-valid-slug>` |
| **strict** | Product INIT (recommended) | `feature/INIT-<AREA>-<NNN>-<slug>` |

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

Manifests: [`qa/manifests/`](../qa/manifests/) (add per initiative).

## Enforcement

See [github-enforcement.md](github-enforcement.md) and [teams-and-rbac.md](teams-and-rbac.md).
