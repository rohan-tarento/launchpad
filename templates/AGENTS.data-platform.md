# Agent guide ({{SERVICE_NAME}})

## Constitution (how to code)

Shared rules: **`.cursor/rules/*.mdc`** (git submodule `your-org/platform-rules`, pinned at **{{RULES_PIN}}**).

Agent skills: **`.agents/skills/`** (seeded from [prayog-skills](https://github.com/drivestream-lab/prayog-skills) @ **{{AGENT_SKILLS_REF}}** via harness sync) — `/spec-feasibility-review`, `/spec-implementation-plan`, `/pre-implement`, `/verify`.

**Do not edit** `.cursor/rules/`. Skill changes go upstream in prayog-skills. Pin record: [`.harness-pin.yaml`](.harness-pin.yaml) (`profile: data-platform`).

---

## Process

Playbook SSOT: **launchpad** `playbook/` (pinned from tenant `<client>-meta`).

| Topic | Where |
|-------|--------|
| SDD workflow | launchpad `playbook/sdd-workflow.md` |
| Harness pins | launchpad `playbook/harness-pins.md` |
| PM ↔ dev handoff | launchpad `playbook/pm-dev-handoff.md` |
| Program board | Your forge engineering board (tenant wiki) |

---

## Product (what to build)

Start here: [`docs/specification/README.md`](docs/specification/README.md)

---

## Run and verify

```bash
make check
make test
{{VERIFY_SMOKE}}
```
