# Agent guide ({{SERVICE_NAME}})

## Constitution (how to code)

Shared rules: **`.cursor/rules/*.mdc`** (git submodule, pinned at **{{RULES_PIN}}**).

Agent skills: **`.agents/skills/`** (seeded from [prayog-skills](https://github.com/drivestream-lab/prayog-skills) @ **{{AGENT_SKILLS_REF}}** via harness sync) — {{AGENT_SKILLS_SLASH_LIST}}.

**Do not edit** `.cursor/rules/`. Skill changes go upstream in prayog-skills.
Pin record: [`.harness-pin.yaml`](.harness-pin.yaml) (`profile: {{PROFILE}}`).

---

## Process

Playbook SSOT: **launchpad** `playbook/` (pinned from tenant `<client>-meta`).

| Topic | Where |
|-------|--------|
| Branching policy + short-code rule | launchpad `playbook/branching-policy.md` |
| PM ↔ dev handoff + sign-off workflow | launchpad `playbook/pm-dev-handoff.md` |
| Delivery model (1:1 wave rule) | launchpad `playbook/delivery-model.md` |
| SDD workflow | launchpad `playbook/sdd-workflow.md` |
| Harness pins | launchpad `playbook/harness-pins.md` |
| Program board | Your forge engineering board (tenant wiki) |

**PRs:** use `.github/pull_request_template.md` — Initiative, Spec path, Verify command.

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
{{CHECK_COMMAND}}
{{TEST_COMMAND}}

{{VERIFY_SMOKE}}
```

{{SETUP_NOTES}}

---

## Before changing behavior

1. Read `AGENTS.md` and relevant **product** spec (and **ADR** if architecture changes).
2. Read **as-built** — do not assume a feature exists without checking.
3. `/pre-implement` before coding — gate check + pre-flight.
4. `/loop-spec` during implementation — verify after each task, fix before moving on.
5. `/ground-spec` when wave is complete — validates FRs, produces contracts for next wave.
6. Update spec, tests, and as-built in the **same PR**.
