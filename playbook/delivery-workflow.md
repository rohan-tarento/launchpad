# Delivery workflow

How an initiative moves from PRD to shipped code in this platform.
Read this before starting any new initiative.

**Related:** [pm-dev-handoff.md](pm-dev-handoff.md) · [skills-matrix.md](skills-matrix.md) · [branching-policy.md](branching-policy.md)

---

## Two workspaces, two roles

| Role | Workspace | Owns |
|------|-----------|------|
| **PM / PO** | `<client>-meta` in Cursor | PRD, impact map, prd-handoff PRs (PRD link only — no spec files) |
| **Dev / Engineering** | App repo in Cursor | Spec, feasibility, technical review, plan, board seed, wave implementation |

**PM never writes spec files. Dev never writes PRD files.**

---

## The skill chain — in execution order

### PM phase (`<client>-meta` workspace)

| Step | Skill | Output |
|------|-------|--------|
| 1 | `/prd` | `prd/INIT-*.md` — feature language, user stories |
| 2 | `/validate-requirements` | Validation report — completeness and consistency check |
| 3 | `/review-findings` | PM decisions on each finding |
| 4 | `/update-documents` | Refined PRD |
| 5 | `/prd-impact-map` | Impact map PR comment — affected repos, merge order, tech lead LGTM |
| 6 | *(PM opens prd-handoff PRs)* | One PR per affected repo — PRD link + plain-English scope |

### Dev phase (app repo workspace)

| Step | Skill | Output |
|------|-------|--------|
| 7 | `/spec-draft` | `docs/specification/product/INIT-*.md` + `02-api-contract.md` — spec slice only; does **not** touch `as-built` |
| 8 | `/initiative-feasibility` | Feasibility report saved to `docs/specification/reports/` on prd-handoff branch; 4-lane triage (PM questions → prd-handoff PR comment) |
| 9 | `/spec-technical-review` | TDD + draft ADRs — **conditional**: run only when feasibility has NEW-ADR findings; PE opens `chore/INIT-{COMPONENT}-{NUMBER}-technical-review` PR, PE approves |
| 10 | `/spec-implementation-plan` | Wave plan + §9 WorkManifest YAML; dev opens `chore/INIT-{COMPONENT}-{NUMBER}-plan` PR; `@dev-leads` approves |
| 11 | *(Dev seeds board — after plan PR merged)* | `gh issue create` — one issue per wave (`W0`, `W1`, …) from §9 YAML; optional `launchpad seed-work` for multi-repo |

### Wave loop (per wave W0 → Wn)

| Step | Skill | Output |
|------|-------|--------|
| 12 | `/pre-implement` | Pre-flight checklist — gate check + contracts from prior wave |
| 13 | `/loop-spec` | Implementation — implement → verify → fix until green |
| 14 | `/ground-spec` | Ground report + §Contracts produced (last commit on wave branch) |
| 15 | *(Human gate)* | Tech lead approves wave PR → as-built W{N} = `human_approved` |

---

## Roles × gates × artifacts

| Gate | Role | GitHub mechanism | Always human? |
|------|------|-----------------|---------------|
| PRD written | PM | meta PR | **Yes** — PM knows product intent |
| Impact map confirmed | Tech lead | "LGTM" comment on meta PR | **Yes** — architectural judgement |
| prd-handoff PRs opened | PM | prd-handoff PR per app repo | Can automate (after tech lead LGTM) |
| Spec slice written | Dev | committed to prd-handoff branch | Can automate (Phase B) |
| Feasibility report | Dev | PR comment on prd-handoff PR | Can automate (Phase A — `@claude` trigger) |
| PM questions answered | PM | PR comment on prd-handoff PR | **Yes** — product decisions |
| Domain questions answered | Domain SME | Slack / GitHub issue | **Yes** — business data |
| TDD (PE review) | PE | `chore/INIT-*-technical-review` PR, PE approves | **Yes** — architectural sign-off |
| Implementation plan | Dev | `chore/INIT-*-plan` PR | Can automate (Phase B — PE Approve trigger) |
| Board seeded | Dev | `gh issue create` per wave (`W0`, `W1`, …); optional `launchpad seed-work` | Can automate (Phase B — plan merged trigger) |
| Wave pre-flight | Dev/Agent | Wave issue comment | Can automate (Phase A — issue labeled) |
| Wave implementation | Dev/Agent | Wave branch | Can automate (Phase C — with guardrails) |
| Wave PR reviewed | Tech lead | Wave PR | **Yes** — code + contract quality |
| INIT closure | PM | Epic closed | **Yes** — product acceptance |

---

## Ship criteria — what "done" means at each gate

| Gate | Done when |
|------|-----------|
| PRD | `/validate-requirements` clean; PM decisions recorded; impact map tech-lead LGTM |
| Spec pipeline | prd-handoff PR merged (spec + feasibility + TDD + plan all on develop); board issues created |
| Each wave | Wave PR merged; `as-built` W{N} = `human_approved`; §Contracts produced committed |
| INIT | All waves `human_approved`; live verify passes; PM closes epic |

---

## Automation phases

The platform supports incremental automation via `anthropics/claude-code-action` on GitHub Actions (BYOK with `ANTHROPIC_API_KEY`). Start fully manual. Flip phases as you gain confidence in output quality.

### Day 1 — fully manual

All steps above run by a human in Cursor. Learn the workflow before automating any part of it.

### Phase A — read-only automation (safe to enable first)

No commits. Agent produces reports and posts them as PR/issue comments. Human reviews and acts.

| Step | Trigger | Action | Model |
|------|---------|--------|-------|
| `/prd-impact-map` | meta PR opened (`chore/INIT-*-prd`) | Posts impact map as PR comment | Sonnet |
| `/initiative-feasibility` | `@claude run initiative-feasibility` comment on prd-handoff PR | Posts feasibility report + PM questions | Sonnet |
| `/pre-implement` checklist | Wave issue labeled `in-progress` | Posts pre-flight checklist as issue comment | Sonnet |

### Phase B — doc commits (switch on after Phase A is stable)

Agent commits documentation to branches. Human reviews PR before merging.

| Step | Trigger | Action | Model |
|------|---------|--------|-------|
| `/spec-draft` | Push to `chore/INIT-*-prd-handoff` | Writes spec slice to branch | Sonnet |
| `/spec-implementation-plan` | PE approves TDD PR (`pull_request_review` state=APPROVED) | Writes plan + §WorkManifest YAML, opens plan PR | Sonnet |
| Board seed | Plan PR merged | `gh issue create` per wave item | Haiku |
| `/ground-spec` | `@claude run ground-spec` comment on wave PR | Writes ground report as last commit on wave branch | Sonnet |

### Phase C — code automation (only after Phase B runs cleanly for a full initiative)

Agent implements product code. Requires proven guardrails. Human still reviews every wave PR.

| Step | Trigger | Action | Model | Guards |
|------|---------|--------|-------|--------|
| `/loop-spec` | Pre-implement checklist posted + dev applies `go-ahead` label | Implement → verify → fix loop, opens wave PR when green | Opus | `--max-turns 30`; scoped file list; human reviews wave PR |

### Always human — never automate

| Step | Why |
|------|-----|
| Write PRD | PM knows product intent |
| Review findings (`/review-findings`) | PM decides scope and priority |
| Refine PRD (`/update-documents`) | PM owns the product statement |
| PM answers questions | Product decisions require product judgement |
| Domain SME confirmations | Business data requires domain knowledge |
| PE approves TDD | Architectural sign-off requires engineering judgement |
| Tech lead reviews wave PR | Code quality + contract correctness requires human review |
| INIT closure | PM confirms acceptance criteria are genuinely met |

---

## Tenant customisation

This document is the **kit default**. If your org's process differs, add a `delivery-workflow-{org}.md` delta in your tenant-meta `playbook/` folder. Document only the differences — do not copy this whole file.

Common delta content:
- Your current automation phase (which steps you've switched on)
- Your model choices per phase
- Org-specific team names in the gates table
- Any steps you've consciously decided to skip or modify
