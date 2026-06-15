# Launchpad playbook

Process SSOT for tenant engineering. **Product content** (PRDs, planning, wiki pages) lives in each private `<client>-meta` repo.

## Start here

| Topic | Document |
|-------|----------|
| Spec layout | [spec-layout.md](spec-layout.md) |
| Delivery model (waves) | [delivery-model.md](delivery-model.md) |
| PM ↔ dev handoff | [pm-dev-handoff.md](pm-dev-handoff.md) |
| PM workflow + skills | [pm-workflow.md](pm-workflow.md) |
| GitHub board | [github-project.md](github-project.md) |
| GitLab board (roadmap) | [../docs/multi-forge.md](../docs/multi-forge.md) |
| Harness pins | [harness-pins.md](harness-pins.md) |
| Factory CLI | [python-automation.md](python-automation.md) |
| Bootstrap PAT | [bootstrap-prerequisites.md](bootstrap-prerequisites.md) |

## Agent skills

Install from **[prayog-skills](https://github.com/drivestream-lab/prayog-skills)** — not duplicated in this repo.

## Tenant overrides

Copy [examples/tenant-meta](../examples/tenant-meta/) for empty `prd/`, `planning/`, `programs/`, `work/`, `wiki/`. Add deltas under tenant `playbook/` only when needed.
