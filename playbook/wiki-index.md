# Wiki index (required — BOOTSTRAP M4)

**Published wiki:** tenant <client>-meta/wiki  
**Source files:** `wiki/*.md` in this repo  
**Publish:** `launchpad publish-wiki --apply` (see [wiki-setup.md](wiki-setup.md))

Wiki pages are **navigation only**. Commands, field tables, and checklists live in **<client>-meta** playbook — link below; do not copy blocks into wiki.

Base URL: `tenant <client>-meta/blob/develop/`

---

## Page 0 — Spec structure (mandatory)

**Wiki title:** Example — Spec structure

| Link | Path |
|------|------|
| Spec layout | `playbook/spec-layout.md` |
| SDD workflow | `playbook/sdd-workflow.md` |

---

## Page 1 — PM workflow

**Wiki title:** Example — PM workflow

| Link | Path |
|------|------|
| PM workflow | `playbook/pm-workflow.md` |
| Skills matrix (prayog-skills install) | `playbook/skills-matrix.md` |
| PM ↔ dev handoff | `playbook/pm-dev-handoff.md` |

---

## Page 2 — How we ship

**Wiki title:** Example — How we ship

| Link | Path |
|------|------|
| PM ↔ dev handoff | `playbook/pm-dev-handoff.md` |
| Branching policy | `playbook/branching-policy.md` |
| Board columns + fields | `playbook/github-project.md` |
| PR template | `templates/pull_request_template.md` |

---

## Page 3 — Python dev (example-api)

**Wiki title:** Example — Python dev

| Link | Path |
|------|------|
| Agent guide | `example-org/example-api` → `AGENTS.md` |
| Integration tests | `example-org/example-api` → `tests/README.md` |
| SDD workflow | `playbook/sdd-workflow.md` |
| Skills matrix | `playbook/skills-matrix.md` |

---

## Page 4 — Platform operator

**Wiki title:** Example — Platform operator

| Link | Path |
|------|------|
| PAT + factory CLI | `playbook/python-automation.md` |
| Setup platform | `README.md` (Factory CLI section) |
| Work manifests | `work/INIT-*.yaml` (generated); see [prd/](../prd/) |
| Teams / RBAC | `playbook/teams-and-rbac.md` |

---

## Page 5 — Skills & agents

**Wiki title:** Example — Skills & agents

| Link | Path |
|------|------|
| Skills matrix | `playbook/skills-matrix.md` |
| Skills audition | `playbook/skills-audition.md` |
| Pre-implement (example-api) | `example-org/example-api` → `.cursor/skills/pre-implement/SKILL.md` |
| Verify skill (example-api) | `example-org/example-api` → `.cursor/skills/verify/SKILL.md` |

---

## Maintenance

When playbook paths change, update wiki links only — not wiki body content.
