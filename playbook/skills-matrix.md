# Skills matrix (example-org)

Agent skills and factory commands for Example engineering. **PM pipeline skills** are the same set proven in **drivestream-lab** — install from [drivestream-lab/prayog-skills](https://github.com/drivestream-lab/prayog-skills), not duplicated in this repo.

**Audition:** [skills-audition.md](skills-audition.md)  
**PM workflow:** [pm-workflow.md](pm-workflow.md)

Skills CLI installs to **`.agents/skills/`** (project) or **`~/.agents/skills/`** (global).

**Dev + PM skills SSOT:** [drivestream-lab/prayog-skills](https://github.com/drivestream-lab/prayog-skills). App repos: seeded by [`sync-harness`](harness-pins.md) — `.harness-pin.yaml` + `.agents/skills/` (gitignored).

---

## Two workspaces

| Who | Open in Cursor | Skills |
|-----|----------------|--------|
| **PM / PO** | `<client>-meta` | `prd` + **prayog-skills** (install below) |
| **Developer** | app repo (e.g. `example-api`) | prayog-skills dev bundle via harness — `/spec-feasibility-review`, `/spec-technical-review`, `/spec-implementation-plan`, `/pre-implement`, `/loop-spec`, `/ground-spec`, `/verify` |

---

## PM pipeline (product INIT)

| Phase | Skill | Source | Edits docs? |
|-------|--------|--------|-------------|
| Draft | `prd` | Community — [awesome-copilot](https://github.com/github/awesome-copilot) | Yes — `prd/INIT-*.md` |
| Audit | `validate-requirements` | **prayog-skills** | No — report only |
| Decide | `review-findings` | **prayog-skills** | No — `prd/reports/Resolution-*.md` |
| Apply | `update-documents` | **prayog-skills** | Yes — PRD + spec drafts |
| Re-audit | `validate-requirements` | **prayog-skills** | No — incremental |
| Spec vs PRD (PM) | `validate-requirements` | **prayog-skills** | No — PM on PRD / spec drafts in meta workspace |
| Backlog | `generate-work-manifest` | **prayog-skills** | `work/INIT-*.yaml` — reads PRD `delivery_model` ([delivery-model.md](delivery-model.md)) |
| Board | `launchpad seed-work` | Factory CLI | Issues on Project |

**Spec handoff PRs** (app repo) — dev gate is **`/spec-feasibility-review`** only (harness dev bundle). PRD traceability: spec links Validation report; PM already ran `/validate-requirements` in meta. See [pm-dev-handoff.md](pm-dev-handoff.md).

### Install (from `<client>-meta` root)

```bash
# Community PRD drafter (sole drafter — remove to-prd if present)
npx skills add github/awesome-copilot --skill prd -a cursor -y

# Lab-owned requirements + backlog skills (all at once)
npx skills add drivestream-lab/prayog-skills --skill '*' -a cursor -y

# Optional: discover other workflows
npx skills add vercel-labs/skills --skill find-skills -a cursor -g -y
```

Verify: `npx skills list`

Invoke: `/prd`, `/validate-requirements`, `/review-findings`, `/update-documents`, `/generate-work-manifest`

**Do not** copy prayog-skills into `.cursor/skills/` here — edit upstream in [prayog-skills](https://github.com/drivestream-lab/prayog-skills), push `main`, reinstall.

**Wave delivery:** When PRD `delivery_model: waves`, `generate-work-manifest` emits one task per wave (W0…Wn, PRE*). See [delivery-model.md](delivery-model.md). Agent templates: `templates/INIT-PRD-outline.md`, `templates/INIT-spec-handoff.md`.

---

## PRD refinement loop

```text
prd/INIT-<id>-outline.md
    → /prd                              → prd/INIT-<id>.md
    → /validate-requirements            → prd/reports/Validation-Report-*.md
    → /review-findings                  → prd/reports/Resolution-*.md
    → /update-documents                 → PRD + cross-repo spec drafts
    → /validate-requirements            (incremental; pass prior report)
```

Production sources: merged `docs/specification/product/` and `04-cross-service-contracts.md` in peer repos (not lab `cross-service-lab.md`).

---

## Dev pipeline (app repos)

| Phase | Skill | Where |
|-------|--------|-------|
| Spec feasibility | `spec-feasibility-review` | `.agents/skills/` (prayog-skills @ harness pin) |
| Technical review (PE) | `spec-technical-review` | same |
| Execution plan | `spec-implementation-plan` | same |
| Pre-flight | `pre-implement` | same |
| Implementation loop | `loop-spec` | same |
| Wave grounding | `ground-spec` | same |
| Live proof | `verify` | same |
| SDD | `.cursor/rules/*.mdc` + [sdd-workflow.md](sdd-workflow.md) | rules submodule |

```text
spec PR → /spec-feasibility-review → /spec-technical-review (PE) → merge spec
       → /spec-implementation-plan
board issue → /pre-implement → /loop-spec → /ground-spec → /verify → PR → develop
```

Harness: `launchpad sync-harness --repo <name> --apply` — see [harness-pins.md](harness-pins.md).

Retro closure epics (e.g. **INIT-EXAMPLE-001**): optional `seed-work` from `work/INIT-*.yaml` → dev skills only.

---

## Full INIT path (summary)

```text
PRD loop (meta, prayog-skills)
    → spec handoff PRs per repo (Phase 1 open, Phase 2 merge)
    → /generate-work-manifest → work/INIT-*.yaml
    → launchpad seed-work --apply
    → dev: /pre-implement → /loop-spec → /ground-spec → /verify → feature PRs
```

Detail: [pm-workflow.md](pm-workflow.md) · [pm-dev-handoff.md](pm-dev-handoff.md)

---

## Related

- [agent-prompt-templates.md](agent-prompt-templates.md)
- [github-project.md](github-project.md)
- Lab reference: [launchpad/skills-matrix](https://github.com/drivestream-lab/launchpad/blob/develop/playbook/skills-matrix.md)
