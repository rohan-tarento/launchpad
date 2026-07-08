# Templates (launchpad kit)

Generic files rendered into repos by `apply-harness` and `init-client`.

Tenants copy **overrides only** into `<slug>-meta/templates/` — Launchpad resolves tenant path first, then these kit defaults.

| Path | Used by |
|------|---------|
| `AGENTS.md` | `apply-harness --repo` → app `AGENTS.md` (profile variables `{{CHECK_COMMAND}}`, `{{TEST_COMMAND}}`, `{{SETUP_NOTES}}`, `{{PROFILE}}`, `{{AGENT_SKILLS_SLASH_LIST}}` substituted at sync time) |
| `AGENTS.meta.md` | `apply-harness --meta` → meta repo `AGENTS.md` |
| `harness-pin*.yaml` | `apply-harness` → `.harness-pin.yaml` in the target repo |
| `github/workflows/` | `init-client` → seeded into repo `.github/workflows/` |
| `CODEOWNERS.*` | same |
| `pull_request_template.md` | same |
| `issues/*.yml` | same → `.github/ISSUE_TEMPLATE/` (`*.app.yml` for app profiles) |
| `INIT-PRD-outline.md`, `INIT-spec-PR.md` | PM / dev agents |

Constitution (`.mdc`) lives in private `*-rules` repos pinned as submodules — not here.
