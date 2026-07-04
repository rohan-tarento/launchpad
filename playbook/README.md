# Launchpad playbook

Process SSOT for tenant engineering. **Product content** (PRDs, planning, wiki pages) lives in each private `<client>-meta` repo.

## Start here

| Topic | Document |
|-------|----------|
| **How we ship (start here)** | [delivery-workflow.md](delivery-workflow.md) |
| Spec layout | [spec-layout.md](spec-layout.md) |
| Delivery model (waves) | [delivery-model.md](delivery-model.md) |
| Branching policy | [branching-policy.md](branching-policy.md) |
| PM ↔ dev handoff + sign-off workflow | [pm-dev-handoff.md](pm-dev-handoff.md) |
| PM workflow (pointer) | [pm-workflow.md](pm-workflow.md) |
| Agent skills matrix | [skills-matrix.md](skills-matrix.md) |
| Agent prompt templates | [agent-prompt-templates.md](agent-prompt-templates.md) |
| Skills audition | [skills-audition.md](skills-audition.md) |
| GitHub board | [github-project.md](github-project.md) |
| GitLab / multi-forge | [../docs/multi-forge.md](../docs/multi-forge.md) |
| Harness pins | [harness-pins.md](harness-pins.md) |
| Greenfield app repo | [greenfield-app-repo.md](greenfield-app-repo.md) |
| Factory CLI | [python-automation.md](python-automation.md) |
| Bootstrap PAT + prerequisites | [bootstrap-prerequisites.md](bootstrap-prerequisites.md) |
| GitHub org setup | [github-org-setup.md](github-org-setup.md) |
| GitHub enforcement | [github-enforcement.md](github-enforcement.md) |
| Teams + RBAC | [teams-and-rbac.md](teams-and-rbac.md) |
| SDD workflow | [sdd-workflow.md](sdd-workflow.md) |
| Wiki setup | [wiki-setup.md](wiki-setup.md) |
| Wiki index template | [wiki-index.md](wiki-index.md) |
| Cursor ↔ GitHub connection | [cursor-github-connection.md](cursor-github-connection.md) |
| Exit criteria (bootstrap) | [exit-criteria.md](exit-criteria.md) |
| Test quality program | [test-quality-program.md](test-quality-program.md) |

## Agent skills

Install from **[prayog-skills](https://github.com/drivestream-lab/prayog-skills)** — not duplicated in this repo.

**Dev bundle (v0.3.0):** `spec-feasibility-review`, `spec-technical-review`, `spec-implementation-plan`, `pre-implement`, `loop-spec`, `ground-spec`, `verify`

## Tenant overrides

Copy [examples/tenant-meta](../examples/tenant-meta/) for empty `prd/`, `planning/`, `programs/`, `work/`, `wiki/`. Add deltas under tenant `playbook/` only when needed.
