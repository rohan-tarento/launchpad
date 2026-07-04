# Skills matrix (example-org)

Agent skills and factory commands for Example engineering. **PM pipeline skills** are the same set proven in **drivestream-lab** — install from [drivestream-lab/prayog-skills](https://github.com/drivestream-lab/prayog-skills), not duplicated in this repo.

**Audition:** [skills-audition.md](skills-audition.md)  
**PM workflow:** [pm-workflow.md](pm-workflow.md)

Skills CLI installs to **`.agents/skills/`** (project) or **`~/.agents/skills/`** (global).

**Dev + PM skills SSOT:** [drivestream-lab/prayog-skills](https://github.com/drivestream-lab/prayog-skills). App repos: seeded by [`sync-harness-app`](harness-pins.md) — `.harness-pin.yaml` + `.agents/skills/` (gitignored).

---

## Two workspaces

| Who | Open in Cursor | Skills |
|-----|----------------|--------|
| **PM / PO** | `<client>-meta` | `prd` + **prayog-skills** PM bundle via `sync-harness-meta` |
| **Developer** | app repo (e.g. `example-api`) | prayog-skills dev bundle via harness — `/spec-draft`, `/initiative-feasibility`, `/spec-technical-review`, `/spec-implementation-plan`, `/pre-implement`, `/loop-spec`, `/ground-spec`, `/verify` |

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
| Impact map | `prd-impact-map` | **prayog-skills** | No — PR comment on meta PR |

**Board seeding is dev-owned** — after `/spec-implementation-plan`, dev creates one GitHub Issue per wave (`W0`, `W1`, …) via `gh issue create`. Optional bulk: `launchpad seed-work` from plan §9 YAML (multi-repo). See [delivery-workflow.md](delivery-workflow.md).

**prd-handoff PRs** (app repo) — PM opens PRD-link-only PR per repo; dev runs `/spec-draft` to write spec slice, then `/initiative-feasibility`. PM does **not** write spec files. See [pm-dev-handoff.md](pm-dev-handoff.md).

### Install (from `<client>-meta` root)

```bash
launchpad sync-harness-meta --apply
launchpad verify-harness-meta
```

This installs community `prd` (awesome-copilot) + prayog PM skills into `.agents/skills/` (gitignored). Commit `.harness-pin.yaml`, `skills-lock.json`, `AGENTS.md`.

Manual reinstall (debug only):

```bash
npx skills add github/awesome-copilot --skill prd -a cursor -y
npx skills add drivestream-lab/prayog-skills --skill validate-requirements --skill review-findings --skill update-documents --skill prd-impact-map -a cursor -y
```

Verify: `npx skills list`

Invoke: `/prd`, `/validate-requirements`, `/review-findings`, `/update-documents`, `/prd-impact-map`

**Do not** copy prayog-skills into `.cursor/skills/` here — edit upstream in [prayog-skills](https://github.com/drivestream-lab/prayog-skills), push `main`, reinstall.

**Wave delivery:** When PRD `delivery_model: waves`, dev `/spec-implementation-plan` §9 emits one issue per wave (`W0`…`Wn`). See [delivery-model.md](delivery-model.md) and [delivery-workflow.md](delivery-workflow.md).

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
| Spec feasibility | `initiative-feasibility` | `.agents/skills/` (prayog-skills @ harness pin) |
| Technical review (PE) | `spec-technical-review` | same |
| Execution plan + board seed | `spec-implementation-plan` | same — §9 WorkManifest YAML; dev runs `gh issue create` |
| Pre-flight | `pre-implement` | same |
| Implementation loop | `loop-spec` | same |
| Wave grounding | `ground-spec` | same |
| Live proof | `verify` | same |
| SDD | `.cursor/rules/*.mdc` + [sdd-workflow.md](sdd-workflow.md) | rules submodule |

```text
prd-handoff PR → /spec-draft → /initiative-feasibility → /spec-technical-review (PE) → merge spec
       → /spec-implementation-plan → gh issue create (one issue per wave W0, W1, …)
board issue → /pre-implement → /loop-spec → /ground-spec → /verify → PR → develop
```

Harness: `launchpad sync-harness-app --repo <name> --apply` — see [harness-pins.md](harness-pins.md).

Retro closure epics (e.g. **INIT-EXAMPLE-001**): optional `seed-work` from `work/INIT-*.yaml` → dev skills only.

---

## Full INIT path (summary)

```text
PRD loop (meta, prayog-skills)
    → spec handoff PRs per repo (Phase 1 open, Phase 2 merge)
    → dev: /spec-implementation-plan → gh issue create (or launchpad seed-work for multi-repo)
    → dev: /pre-implement → /loop-spec → /ground-spec → /verify → feature PRs
```

Detail: [pm-workflow.md](pm-workflow.md) · [pm-dev-handoff.md](pm-dev-handoff.md)

---

## Related

- [agent-prompt-templates.md](agent-prompt-templates.md)
- [github-project.md](github-project.md)
- Lab reference: [launchpad/skills-matrix](https://github.com/drivestream-lab/launchpad/blob/develop/playbook/skills-matrix.md)
