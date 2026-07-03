# Spec-driven development workflow (example-org)

How agents and engineers use the **truth hierarchy** in Launchpad repos. Constitution rules live in submodules; product truth lives in each service repo.

**PM ↔ dev handoff:** [pm-dev-handoff.md](pm-dev-handoff.md)

## Hierarchy (read in this order)

| Priority | Location | Answers |
|----------|----------|---------|
| 1 | `.cursor/rules/*.mdc` (submodule) | **How** to build |
| 2 | `AGENTS.md` | Router — rules boundary, verify commands |
| 3 | `docs/specification/product/` | **What** to build |
| 4 | `docs/specification/adr/` | **Why** (accepted decisions) |
| 5 | `docs/specification/as-built/` | **What is live today** — `implementation-status.md`  |

**Mandatory layout:** [spec-layout.md](spec-layout.md) — **no** `docs/specification/harness/`.

## Before changing behavior

1. Read `AGENTS.md`
2. Read relevant **product** spec (and **ADR** if architecture/contracts change)
3. Read **as-built** — do not assume a feature exists because the spec mentions it
4. If the change touches another service, read **04-cross-service-contracts.md** (example-api) or equivalent in peer repos

## Implementation discipline

When code changes, update together:

- product spec (if contract or capability changes)
- **unit tests** — logic and edges (see repo `tests/README.md` for layout)
- **verify** (`tests/verify/`) — live E2E per product feature
- **as-built** — distinguish implemented / unit-tested / live-verified

## PR traceability (required)

Every PR uses the template block:

- Initiative (e.g. `BOOTSTRAP-001`, later `INIT-…`)
- Issue #
- Spec paths touched
- Verify command run

## Example reading order (backend app)

| Step | Path |
|------|------|
| 1 | `AGENTS.md` |
| 2 | `product/00-service-profile.md` → `02-api-contract.md` |
| 3 | `05-roles-and-authz.md` / `03-tenant-and-user-lifecycle.md` as needed |
| 4 | Relevant `adr/` |
| 5 | `as-built/implementation-status.md` |

Integration tests: [`example-api/tests/README.md`](https://github.com/example-org/example-api/blob/develop/tests/README.md)

## Meta references

- Active INIT PRD: `prd/INIT-EXAMPLE-001.md` (in `<client>-meta/prd/`)
- Skills: [skills-matrix.md](skills-matrix.md)
- Agent prompts: [agent-prompt-templates.md](agent-prompt-templates.md)
