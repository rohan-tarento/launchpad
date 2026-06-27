# Agent guide ({{SERVICE_NAME}})

## Constitution (how to code)

Shared rules: **`.cursor/rules/*.mdc`** (git submodule `your-org/frontend-rules`, pinned at **{{RULES_PIN}}**).

Agent skills: **`.agents/skills/`** (seeded from [prayog-skills](https://github.com/drivestream-lab/prayog-skills) @ **{{AGENT_SKILLS_REF}}** via harness sync) — `/spec-feasibility-review`, `/spec-implementation-plan`, `/pre-implement`, `/verify`.

**Do not edit** `.cursor/rules/`. Skill changes go upstream in prayog-skills. Pin record: [`.harness-pin.yaml`](.harness-pin.yaml) (`profile: frontend`).

---

## Process

Playbook SSOT: **launchpad** `playbook/` (tenant `<client>-meta` holds product deltas only).

| Topic | Where |
|-------|--------|
| SDD workflow | launchpad `playbook/sdd-workflow.md` |
| Harness pins | launchpad `playbook/harness-pins.md` |
| PM ↔ dev handoff | launchpad `playbook/pm-dev-handoff.md` |
| Program board | Your forge engineering board (tenant wiki) |

**PRs:** use `.github/pull_request_template.md` — Initiative, Spec path, Verify command.

---

## Product (what to build)

Start here: [`docs/specification/README.md`](docs/specification/README.md)

| Layer | Entry point | Purpose |
|-------|-------------|---------|
| **Product specs** | [`docs/specification/product/`](docs/specification/product/) | Capabilities, route map, initiative specs |
| **As-built** | [`docs/specification/as-built/implementation-status.md`](docs/specification/as-built/implementation-status.md) | Live vs deferred; verification matrix |
| **ADRs** | [`docs/specification/adr/README.md`](docs/specification/adr/README.md) | Architecture decisions |

Route trees and upstream service names belong in **product specs** — not in cursor rules.

---

## Run and verify

- Setup and run: [`README.md`](README.md)
- Test harness: [`tests/README.md`](tests/README.md)

```bash
npm run lint
npm run test
npm run build

{{VERIFY_SMOKE}}
```

---

## Before changing behavior

1. Read `AGENTS.md` and relevant **product** spec (and **ADR** if architecture/contracts change).
2. Read **as-built** — do not assume a feature exists because the spec mentions it.
3. Update spec, tests, and as-built in the **same PR**.
4. `/spec-feasibility-review` → `/spec-implementation-plan` → `/pre-implement` → `/verify` per harness skills.
