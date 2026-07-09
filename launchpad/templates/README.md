# Templates (launchpad kit)

Reference files for tenant overrides and manual repo setup.

Tenants copy **overrides only** into `<slug>-meta/templates/` — Launchpad resolves tenant path first, then these kit defaults when seeding via `apply-harness`.

---

## Seeded by `apply-harness` (v0.5.10)

| Artifact | Source template | Destination |
|----------|-----------------|-------------|
| CODEOWNERS | `CODEOWNERS.<stack>` from harness profile | `.github/CODEOWNERS` |
| Harness pin | `harness-pin.<stack>.yaml` from harness profile | `.harness-pin.yaml` |
| Constitution | rules repo URL from harness profile | `.cursor/rules/` submodule |
| Skills | skill repos from harness profile | `.agents/skills/<repo>/` submodules |

Substitutes `example-org` → actual GitHub org from `programme.yaml` in CODEOWNERS.

---

## CODEOWNERS (per stack)

| File | Stack |
|------|-------|
| `CODEOWNERS.python-backend` | `python-backend` |
| `CODEOWNERS.nextjs-frontend` | `nextjs-frontend` |
| `CODEOWNERS.data-platform` | `data-platform` |
| `CODEOWNERS.meta-pm` | `meta-pm` (meta repo) |

---

## Harness pin skeletons (per stack)

| File | Stack |
|------|-------|
| `harness-pin.python-backend.yaml` | `python-backend` |
| `harness-pin.nextjs-frontend.yaml` | `nextjs-frontend` |
| `harness-pin.data-platform.yaml` | `data-platform` |
| `harness-pin.meta.yaml` | `meta-pm` (meta repo) |

---

## Reference copies (manual deploy in v0.5.10)

Copy into each repo as needed. See [playbook/github-enforcement.md](../../playbook/github-enforcement.md).

### GitHub workflows

| File | Purpose |
|------|---------|
| `github/workflows/ci.yml` | Placeholder CI — job name `ci` for required checks |
| `github/workflows/policy-branch-name.yml` | Branch name validation on PRs to `develop` |
| `github/workflows/policy-merge-source.yml` | Merge-source validation on PRs to `main` |

### Issue templates

`*.app.yml` variants are for app repos; plain `*.yml` for the meta repo.

| File | Type |
|------|------|
| `issues/feature.yml` / `feature.app.yml` | New capability |
| `issues/bug.yml` / `bug.app.yml` | Defect |
| `issues/chore.yml` / `chore.app.yml` | Non-functional work |
| `issues/config.yml` / `config.app.yml` | Config / infra change |

### Agent guides and PR template

| File | Typical use |
|------|-------------|
| `AGENTS.md` | App repo agent router (customize per repo) |
| `AGENTS.meta.md` | Meta repo agent router |
| `pull_request_template.md` | `.github/pull_request_template.md` |
| `INIT-PRD-outline.md` | PM PRD starter doc |
| `INIT-spec-PR.md` | Spec PR description template |

---

Constitution (`.mdc`) lives in `*-rules` repos pinned as git submodules — not in this folder.
