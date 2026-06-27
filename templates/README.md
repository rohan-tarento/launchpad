# Templates (launchpad kit)

Generic files rendered into app repos by `sync-harness` and `setup-gitflow --with-templates`.

Tenants copy **overrides only** into `<client>-meta/templates/` — launchpad resolves tenant path first, then these kit defaults.

| Path | Used by |
|------|---------|
| `AGENTS.{python,frontend,data-platform}.md` | `sync-harness` → app `AGENTS.md` |
| `harness-pin*.yaml` | `sync-harness` → app `.harness-pin.yaml` |
| `github/workflows/` | `setup-gitflow --with-templates` |
| `CODEOWNERS.*` | same |
| `pull_request_template.md` | same |
| `INIT-PRD-outline.md`, `INIT-spec-handoff.md` | PM agents in `<client>-meta` |

Constitution (`.mdc`) lives in private `*-rules` repos — not here.
