# Agent guide ({{SERVICE_NAME}})

## Constitution (how to code)

Shared rules: **`.cursor/rules/*.mdc`** (git submodule `your-org/service-rules`, pinned at **{{RULES_PIN}}**).

Agent skills: **`.agents/skills/`** (seeded from [prayog-skills](https://github.com/drivestream-lab/prayog-skills) @ **{{AGENT_SKILLS_REF}}** via harness sync) — `/spec-feasibility-review`, `/spec-implementation-plan`, `/pre-implement`, `/verify`.

**Do not edit** `.cursor/rules/`. Skill changes go upstream in prayog-skills. Pin record: [`.harness-pin.yaml`](.harness-pin.yaml).

---

## Process

Playbook SSOT: **launchpad** `playbook/` (pinned from tenant `<client>-meta`).

| Topic | Where |
|-------|--------|
| SDD workflow | launchpad `playbook/sdd-workflow.md` |
| Branching policy + short-code rule | launchpad `playbook/branching-policy.md` |
| PM ↔ dev handoff + sign-off workflow | launchpad `playbook/pm-dev-handoff.md` |
| Harness pins | launchpad `playbook/harness-pins.md` |
| Program board | Your forge engineering board (tenant wiki) |

**PRs:** use `.github/pull_request_template.md` — Initiative, Spec path, Verify command.
**CODEOWNERS:** seeded from `launchpad/templates/CODEOWNERS.backend` (or profile variant) — gate enforcement per `pm-dev-handoff.md § Sign-off workflow`.

---

## Product (what to build)

Start here: [`docs/specification/README.md`](docs/specification/README.md)

| Layer | Entry point | Purpose |
|-------|-------------|---------|
| **Product specs** | [`docs/specification/product/`](docs/specification/product/) | What this service does |
| **As-built** | [`docs/specification/as-built/implementation-status.md`](docs/specification/as-built/implementation-status.md) | Live vs deferred; verification matrix |
| **ADRs** | [`docs/specification/adr/README.md`](docs/specification/adr/README.md) | Architecture decisions |

Active work: board issue **Spec path** → product initiative spec (from PRD handoff).

---

## Run and verify

- Setup and run: [`README.md`](README.md)
- Integration verify: [`tests/README.md`](tests/README.md)

```bash
make check
make test

conda activate {{CONDA_ENV}}
{{VERIFY_SMOKE}}
```

---

## Before changing behavior

1. Read `AGENTS.md` and relevant **product** spec (and **ADR** if needed).
2. Read **as-built** — do not assume features exist without checking.
3. Update spec, tests, and as-built in the **same PR**.
4. `/spec-feasibility-review` → (PE: `/spec-technical-review` when needed) → `/spec-implementation-plan` → `/pre-implement` → `/loop-spec` → `/ground-spec` → `/verify` per harness skills and `pm-dev-handoff.md`.
