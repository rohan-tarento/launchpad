# Templates (launchpad kit)

Generic files seeded into repos by `apply-harness` and `init-client`.

Tenants copy **overrides only** into `<slug>-meta/templates/` — Launchpad resolves tenant path first, then these kit defaults.

---

## CODEOWNERS (per stack)

`apply-harness` picks the right file based on the repo's stack profile and writes it as `.github/CODEOWNERS`.
Substitutes `example-org` → actual GitHub org from `programme.yaml`.

| File | Stack | Dropped into repo |
|------|-------|-------------------|
| `CODEOWNERS.python-backend` | `python-backend` | `.github/CODEOWNERS` |
| `CODEOWNERS.nextjs-frontend` | `nextjs-frontend` | `.github/CODEOWNERS` |
| `CODEOWNERS.data-platform` | `data-platform` | `.github/CODEOWNERS` |
| `CODEOWNERS.meta-pm` | `meta-pm` (meta repo) | `.github/CODEOWNERS` |

Each file protects: spec reports (Technical-Review, Implementation-Plan, Ground-Report), product specs, ADRs, as-built docs, constitution, and source paths.

---

## Harness pin skeletons (per stack)

`apply-harness` seeds `.harness-pin.yaml` into new repos (skips if already present).

| File | Stack |
|------|-------|
| `harness-pin.python-backend.yaml` | `python-backend` |
| `harness-pin.nextjs-frontend.yaml` | `nextjs-frontend` |
| `harness-pin.data-platform.yaml` | `data-platform` |
| `harness-pin.meta.yaml` | `meta-pm` (meta repo) |

---

## GitHub workflows

Seeded into `.github/workflows/` by `init-client`.

| File | Purpose |
|------|---------|
| `github/workflows/ci.yml` | Placeholder CI — job name `ci` is required for branch protection |
| `github/workflows/policy-branch-name.yml` | Validates `feature/INIT-{COMPONENT}-{NUMBER}-{slug}` on PRs to `develop` |
| `github/workflows/policy-merge-source.yml` | Blocks PRs to `main` not from `develop`/`release/*`/`hotfix/*` |

---

## Issue templates

Seeded into `.github/ISSUE_TEMPLATE/` by `init-client`.
`*.app.yml` variants are for app repos; plain `*.yml` for the meta repo.

| File | Type |
|------|------|
| `issues/feature.yml` / `feature.app.yml` | New capability |
| `issues/bug.yml` / `bug.app.yml` | Defect |
| `issues/chore.yml` / `chore.app.yml` | Non-functional work |
| `issues/config.yml` / `config.app.yml` | Config / infra change |

---

## Agent guides and PR template

| File | Seeded as |
|------|-----------|
| `AGENTS.md` | App repo `AGENTS.md` (variables substituted at harness sync) |
| `AGENTS.meta.md` | Meta repo `AGENTS.md` |
| `pull_request_template.md` | `.github/pull_request_template.md` |
| `INIT-PRD-outline.md` | PM PRD starter doc |
| `INIT-spec-PR.md` | Spec PR description template |

---

Constitution (`.mdc`) lives in private `*-rules` repos pinned as git submodules — not here.
