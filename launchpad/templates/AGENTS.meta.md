# Agent guide ({{DISPLAY_NAME}} meta)

PM workspace for **{{ORG}}** (`{{META_REPO}}`).

## Agent skills

Installed under **`.harness/skills/<skill>/`** (hub) mirrored to **`.agents/skills/`** and **`.claude/skills/`**:

- Community: `/prd` @ awesome-copilot
- Prayog PM bundle @ **{{AGENT_SKILLS_REF}}**: {{AGENT_SKILLS_SLASH_LIST}}

Pin record: [`.harness-pin.yaml`](.harness-pin.yaml) (`profile: meta-pm`).

Re-sync after clone: `launchpad apply-harness --meta --apply`

---

## Process

Playbook SSOT: **launchpad** `playbook/` (from tenant meta or pip install).

| Topic | Where |
|-------|--------|
| PM workflow | launchpad `playbook/pm-workflow.md` |
| Delivery workflow | launchpad `playbook/delivery-workflow.md` |
| Skills matrix | launchpad `playbook/skills-matrix.md` |
| Harness pins | launchpad `playbook/harness-pins.md` |
| Program board | Your forge engineering board |

---

## Product pipeline

| Phase | Skill | Output |
|-------|--------|--------|
| Draft | `/prd` | `prd/INIT-<id>.md` |
| Audit | `/validate-requirements` | `prd/reports/Validation-Report-*.md` |
| Decide | `/review-findings` | `prd/reports/Resolution-*.md` |
| Apply | `/update-documents` | PRD + cross-repo spec drafts |
| Impact | `/prd-impact-map` | Impact map PR comment — affected repos, merge order |

Engineering opens **spec PRs** in app repos after impact map LGTM. Devs run dev harness skills in app repos — not here.

See launchpad `playbook/delivery-workflow.md`.
