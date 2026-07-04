# Agent prompt templates

Copy-paste starters for Cursor Agent. **Use the section for your role** — workspace and skills differ.

**Skills:** [skills-matrix.md](skills-matrix.md) · **Handoff:** [pm-dev-handoff.md](pm-dev-handoff.md) · **Audition:** [skills-audition.md](skills-audition.md)

---

## Who uses what

| Role | Open in Cursor | Skills | Typical work |
|------|----------------|--------|--------------|
| **Product owner / PM** | `<client>-meta` | `/prd`, `/validate-requirements`, `/review-findings`, `/update-documents`, `/prd-impact-map`, `/generate-work-manifest` | PRD writing, impact mapping, prd-handoff PRs (PRD link only — no spec files) |
| **Developer** | App repo (e.g. `example-api`) | `/spec-draft`, `/initiative-feasibility`, `/spec-technical-review`, `/spec-implementation-plan`, `/pre-implement`, `/loop-spec`, `/ground-spec`, `/verify` | Writes spec, reviews buildability, PE lane, plan, board seed, implementation, wave grounding |

**Board:** cite **GitHub issue #** and **full title** — not manifest ids (`Q1`, `T2`) in conversation.

---

# Product owner / PM prompts

**Workspace:** `<client>-meta` (not example-api).  
**Install once:** [skills-matrix.md](skills-matrix.md) — `prd` + `prayog-skills` bundle.

---

## 1 — Draft PRD (new product INIT)

**When:** Phase 1 — new initiative, no merged PRD yet.  
**Branch:** `chore/INIT-<id>-prd` from `develop`

```text
Initiative: INIT-EXAMPLE-002 (proposed)
Branch: chore/INIT-EXAMPLE-002-prd from develop

/prd

Follow templates/INIT-PRD-outline.md and playbook/delivery-model.md.
Declare delivery_model: waves | repo-slice.
If waves: include §4.0 Delivery model + §4.5 Implementation waves (W0, W1, …).

Outline:
- Goal: (one sentence)
- Repos affected: example-api, example-registry, …
- Constraints: (timeline, out of scope)

Output: prd/INIT-EXAMPLE-002.md only. No application code.
```

---

## 2 — Validate PRD

**When:** After draft PRD or outline exists.  
**Output:** `prd/reports/Validation-Report-INIT-*.md`

```text
/validate-requirements

Initiative: INIT-EXAMPLE-002
Primary doc: prd/INIT-EXAMPLE-002-outline.md
Also read:
- example-api docs/specification/product/04-cross-service-contracts.md
- (other affected repo product specs)

Report: prd/reports/Validation-Report-INIT-EXAMPLE-002.md
Read-only unless I ask to apply fixes.
```

---

## 3 — Review validation findings

**When:** Validation report has open items; PM decides accept / defer / fix.

```text
/review-findings

Report: prd/reports/Validation-Report-INIT-EXAMPLE-002.md
Primary doc: prd/INIT-EXAMPLE-002.md

Output: prd/reports/Resolution-INIT-EXAMPLE-002.md with decisions per finding.
Do not edit PRD until I confirm resolution.
```

---

## 4 — Apply PRD fixes

**When:** Resolution report approved; update PRD and spec drafts on PR branch.

```text
/update-documents

Resolution: prd/reports/Resolution-INIT-EXAMPLE-002.md
Update: prd/INIT-EXAMPLE-002.md
Also align: (list spec paths on open PR branches if any)
```

---

## 5 — Spec handoff PR (product INIT — one repo)

**When:** Phase 1 — PM opens docs-only PR per app repo. **Dev merges** — PM does not merge app `develop`.  
**Branch:** `chore/INIT-<id>-spec-handoff-<repo>` from app `develop`

```text
Initiative: INIT-EXAMPLE-002
Repo: example-api
Branch: chore/INIT-EXAMPLE-002-spec-handoff-example-api from develop

Start from <client>-meta/templates/INIT-spec-handoff.md (wave IDs must match PRD §4.0).
Gate: playbook/spec-layout.md § INIT spec handoff.

Update docs/specification/product/ only:
- product/INIT-EXAMPLE-002.md (slice for this repo)
- 02-api-contract.md deltas if routes change
- 04-cross-service-contracts.md if integrations change

No src/. No tests/.
Link meta PRD: prd/INIT-EXAMPLE-002.md (meta PR branch or develop after Phase 2 merge).

# Note: /validate-requirements is PM-only (meta workspace). Dev opens PR; PM runs validation in meta.
```

---

## 6 — Spec vs PRD conformance (PM only — meta workspace)

**When:** PM validates spec drafts against PRD **before** opening spec handoff PRs (or after `/update-documents`). **Not** seeded in app-repo harness.

```text
/validate-requirements

Initiative: INIT-EXAMPLE-002
Primary doc: prd/INIT-EXAMPLE-002.md on <client>-meta develop
Spec draft: product/INIT-EXAMPLE-002.md on handoff branch (or pasted path)
Check: repo spec slice matches PRD.
Report only — list gaps; do not merge spec PR until clean.
```

**Dev on prd-handoff PR:** runs `/spec-draft` → `/initiative-feasibility` → PE `/spec-technical-review` → `/spec-implementation-plan`. PM does **not** write spec files. Dev does **not** run `/validate-requirements` (PM-only in meta).

---

## 7 — Generate work manifest (after Phase 2 merges)

**When:** Meta PRD + all spec PRs merged to `develop`.  
**Output:** `work/INIT-*.yaml`

```text
/generate-work-manifest

PRD: prd/INIT-EXAMPLE-002.md on <client>-meta develop
Read delivery_model from PRD §4.0 (playbook/delivery-model.md).
If delivery_model: waves — one manifest task per wave ID (W0, W1, …, PRE* from merged spec).
If delivery_model: repo-slice — one task per repo (v1).

Merged spec paths:
- example-registry docs/specification/product/INIT-EXAMPLE-002.md
- (other repos)

Output: work/INIT-EXAMPLE-002.yaml
apiVersion: launchpad/v1 (see work/INIT-EXAMPLE-001.yaml).
Include dry-run seed command; do not run seed-work unless I ask.
```

**Terminal (PM):** after manifest PR merges:

```bash
launchpad seed-work --config work/INIT-EXAMPLE-002.yaml --dry-run
launchpad seed-work --config work/INIT-EXAMPLE-002.yaml --apply
```

---

## 8 — INIT retro — spec handoff (chore closure)

**When:** PRD signed off; retro closure like **INIT-EXAMPLE-001** (implementation already on `develop`).  
**One PR** per repo — dev merges; **no `src/`**.

```text
Initiative: INIT-EXAMPLE-001
Repo: example-api
Branch: chore/INIT-EXAMPLE-001-spec-handoff-example-api from develop

Add docs/specification/product/INIT-EXAMPLE-001.md:
- Status Closed / retro; link to <client>-meta prd/INIT-EXAMPLE-001.md
- As-delivered wave table (#27–#32) + dev read order
- Delete superseded product quality spec; update README + tests/README header

No src/. No tests/.

PR title: [spec] handoff — INIT-EXAMPLE-001 — example-api
Label: spec
```

**PRD:** `prd/INIT-EXAMPLE-001.md` (in `<client>-meta/prd/`)

---

# Developer prompts

**Workspace:** app repo root (e.g. **`example-api`**), branch `develop` (or feature branch from develop).  
**Skills:** prayog-skills dev bundle in `.agents/skills/` (seeded by `sync-harness-app`).  
**Do not** edit `.cursor/rules/` submodule — propose upstream in service-rules. Skill changes → [prayog-skills](https://github.com/drivestream-lab/prayog-skills).

**Read first:** `AGENTS.md` → board issue **Spec path** → `docs/specification/as-built/`.

---

## D1 — Product INIT — implementation slice

**When:** Board issue from seeded INIT epic; spec handoff already on `develop`.  
**One issue = one PR.**

```text
Initiative: INIT-EXAMPLE-002
Issue: #42 — [feature] Short title from GitHub
Repo: example-api (this workspace)

/pre-implement

Read:
- AGENTS.md
- docs/specification/product/INIT-EXAMPLE-002.md
- docs/specification/product/02-api-contract.md (if routes)
- docs/specification/as-built/implementation-status.md

Execute one slice:
1. Implement code + tests (unit vs verify — no overlap)
2. Update product spec status if behavior ships
3. Update as-built/implementation-status.md in same PR
4. Run board Verify command

Branch: feature/INIT-EXMPL-002-w{N}-{slug}  ← see branching-policy.md
Verify: (paste from board — e.g. make check && poetry run python -m tests.verify.verify_all)

Do not edit .cursor/rules/ submodule.
```

---

## D2 — Test maintenance chore (post–INIT-EXAMPLE-001)

**When:** Future test work on example-api after **INIT-EXAMPLE-001** retro closure. Waves W1–W5 are **done** — do not re-run.  
**Handoff SSOT:** `docs/specification/product/INIT-EXAMPLE-001.md`

```text
Initiative: INIT-EXAMPLE-001
Issue: #<n> — [chore] <test area>
Repo: example-api (this workspace)

/pre-implement

Read:
- docs/specification/product/INIT-EXAMPLE-001.md (dev read order)
- docs/specification/product/<relevant capability>.md
- docs/specification/as-built/implementation-status.md (## Testing harness)
- tests/README.md

Deliver per overlap rules: unit and/or verify trim; update feature map + as-built.

Branch: chore/INIT-EXAMPLE-001-<slug>
Verify: make test (or board Verify command)

Do not edit .cursor/rules/ submodule. No new product features unless scoped.
```

### Historical wave reference (complete — do not re-implement)

| Wave | Product spec | Verify |
|------|--------------|--------|
| W1 auth | `05-roles-and-authz.md` | `make test` |
| W2 onboarding | `03-tenant-and-user-lifecycle.md` | `make test` |
| W3 device/OTP | `06-device-traffic-and-mqtt.md` | `make test` |
| W4 bridge | `06-device-traffic-and-mqtt.md` | `make test` |
| W5 close-out | `tests/README.md` | `make check && poetry run python -m tests.verify.verify_all` |

---

## D3 — prd-handoff PR (dev writes spec, reviews, plans)

**When:** PM opened prd-handoff PR with PRD link + plain-English scope. Dev writes spec, checks buildability, gets PE technical review, then produces plan.  
**Workspace:** app repo, checkout the prd-handoff PR branch.

### D3a — Write spec slice (first)

```text
/spec-draft

Initiative: INIT-EXAMPLE-003
PRD: <client>-meta/prd/INIT-EXAMPLE-003.md  (linked in prd-handoff PR body)
Scope: (paste PM's plain-English scope from prd-handoff PR body)
Repo: example-registry (this workspace)

Output: docs/specification/product/INIT-EXAMPLE-003.md
Review and edit before committing — this is a draft.
```

### D3b — Review buildability (after committing spec draft)

```text
/initiative-feasibility

Initiative: INIT-EXAMPLE-003
Spec: docs/specification/product/INIT-EXAMPLE-003.md
PRD: <client>-meta/prd/INIT-EXAMPLE-003.md

Output: docs/specification/reports/Initiative-Feasibility-Report-INIT-EXAMPLE-003.md
Post PM questions as PR comments on prd-handoff PR (plain English, no jargon).
Route PE questions to /spec-technical-review. Auto-fix naming drift.
```

### D3c — PE technical review (when feasibility has PE questions / NEW-ADR)

```text
/spec-technical-review

Initiative: INIT-EXAMPLE-003
Feasibility report: docs/specification/reports/Initiative-Feasibility-Report-INIT-EXAMPLE-003.md
Spec: docs/specification/product/INIT-EXAMPLE-003.md

Output: docs/specification/reports/Technical-Review-INIT-EXAMPLE-003.md
Resolves engineering decisions, drafts ADRs.
PE opens a separate PR for this — PE approves it.
```

### D3d — Implementation plan (after PE approves TDD)

```text
/spec-implementation-plan

Initiative: INIT-EXAMPLE-003
Technical review: docs/specification/reports/Technical-Review-INIT-EXAMPLE-003.md
Feasibility report: docs/specification/reports/Initiative-Feasibility-Report-INIT-EXAMPLE-003.md
Spec: docs/specification/product/INIT-EXAMPLE-003.md

Output: docs/specification/reports/Implementation-Plan-INIT-EXAMPLE-003.md
Includes §WorkManifest YAML — dev runs gh issue create to seed board.
```

---

## D4 — Verify only (post-implementation)

**When:** Code done; run board verify before opening PR or after CI.

```text
/verify

Initiative: INIT-EXAMPLE-001
Issue: #<n>
Verify command: make test

Run the command; report pass/fail and any fixes needed.
```

Live stack example:

```text
/verify

Initiative: INIT-EXAMPLE-002
Issue: #42
Verify command: make check && poetry run python -m tests.verify.verify_all

conda activate example-api required for verify_all.
```

---

## D5 — Cross-service check

**When:** Issue touches HTTP routes, JWT claims, or peer integrations.

```text
Initiative: INIT-EXAMPLE-002
Issue: #42
Repo: example-api (this workspace)

Before implementing:
Read docs/specification/product/04-cross-service-contracts.md
Read example-registry docs/specification/product/ (relevant integration doc)

Confirm example-api changes do not break EMQX auth, device validation, or Kafka bridge contracts.
```

---

## D6 — Wave implementation (implement → verify → ground)

**When:** Board wave issue is In Progress; pre-implement checklist is done.  
**One wave = one PR.** Ground report is the last commit before PR is marked ready.

```text
Initiative: INIT-EXAMPLE-002
Issue: #42 — [INIT-EXMPL-002 W1] extraction engine
Repo: example-api (this workspace)
Branch: feature/INIT-EXMPL-002-w1-extraction (already open from /pre-implement)

/loop-spec

Implement W1 tasks in order from plan.
Run {check_command} and {test_command} after each task.
Fix failures before moving on. Stop when all tasks green.
Do not implement W2 scope.
```

When loop exits green:

```text
/ground-spec

Spec: 01  (or wave W1 of INIT-EXAMPLE-002)
Commit ground report as last commit on feature/INIT-EXMPL-002-w1-extraction.
Open PR: "[INIT-EXMPL-002 W1] extraction engine — implementation + ground report"
```

---

## D7 — Harness / platform chore (bootstrap — reference)

**When:** BOOTSTRAP-001-style harness work in app repo (historical).

```text
Initiative: BOOTSTRAP-001
Repo: example-api
Task: Harness only — no product features.

/pre-implement

Deliverables: AGENTS.md links to <client>-meta playbook; .agents/skills; PR template; as-built columns.
Verify: make check
```

---

## PR traceability (both roles)

Every PR description should match board fields:

| Field | Example |
|-------|---------|
| Initiative | `INIT-EXAMPLE-001` or `INIT-EXAMPLE-002` |
| Issue | `#<n>` |
| Spec path | `docs/specification/product/INIT-EXAMPLE-001.md` |
| Verify command | `make test` |

Template: app repo `.github/pull_request_template.md`
