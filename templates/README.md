# Templates (launchpad kit)

Generic files rendered into app repos by `sync-harness` and `setup-gitflow --with-templates`.

Tenants copy **overrides only** into `<client>-meta/templates/` — launchpad resolves tenant path first, then these kit defaults.

| Path | Used by |
|------|---------|
| `AGENTS.md` | `sync-harness` → app `AGENTS.md` (single unified template; profile variables `{{CHECK_COMMAND}}`, `{{TEST_COMMAND}}`, `{{SETUP_NOTES}}`, `{{PROFILE}}`, `{{AGENT_SKILLS_SLASH_LIST}}` substituted at sync time) |
| `harness-pin*.yaml` | `sync-harness` → app `.harness-pin.yaml` |
| `github/workflows/` | `setup-gitflow --with-templates` |
| `CODEOWNERS.*` | same |
| `pull_request_template.md` | same |
| `issues/*.yml` | same → `.github/ISSUE_TEMPLATE/` (`*.app.yml` for app profiles) |
| `INIT-PRD-outline.md`, `INIT-spec-handoff.md` | PM agents in `<client>-meta` |

Constitution (`.mdc`) lives in private `*-rules` repos — not here.
