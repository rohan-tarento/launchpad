# Agent prompt templates

Copy-paste starters for Cursor Agent. **Use the section for your role** — workspace and skills differ.

**Skills:** [skills-matrix.md](skills-matrix.md) · **Handoff:** [pm-dev-handoff.md](pm-dev-handoff.md) · **Audition:** [skills-audition.md](skills-audition.md)

---

## Who uses what

| Role | Open in Cursor | Skills | Typical work |
|------|----------------|--------|--------------|
| **Product owner / PM** | `<client>-meta` | `/prd`, `/validate-requirements`, `/review-findings`, `/update-documents`, `/generate-work-manifest` | PRD, spec handoff PRs, work manifests, `seed-work` |
| **Developer** | App repo (e.g. `example-api`) | `/spec-feasibility-review`, `/spec-implementation-plan`, `/pre-implement`, `/verify` | Spec review, plan, implementation PRs, tests, as-built |

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
Initiative: INIT-DS-002 (proposed)
Branch: chore/INIT-DS-002-prd from develop

/prd

Follow templates/INIT-PRD-outline.md and playbook/delivery-model.md.
Declare delivery_model: waves | repo-slice.
If waves: include §4.0 Delivery model + §4.5 Implementation waves (W0, W1, …).

Outline:
- Goal: (one sentence)
- Repos affected: example-api, example-registry, …
- Constraints: (timeline, out of scope)

Output: prd/INIT-DS-002.md only. No application code.
```

---

## 2 — Validate PRD

**When:** After draft PRD or outline exists.  
**Output:** `prd/reports/Validation-Report-INIT-*.md`

```text
/validate-requirements

Initiative: INIT-DS-002
Primary doc: prd/INIT-DS-002-outline.md
Also read:
- example-api docs/specification/product/04-cross-service-contracts.md
- (other affected repo product specs)

Report: prd/reports/Validation-Report-INIT-DS-002.md
Read-only unless I ask to apply fixes.
```

---

## 3 — Review validation findings

**When:** Validation report has open items; PM decides accept / defer / fix.

```text
/review-findings

Report: prd/reports/Validation-Report-INIT-DS-002.md
Primary doc: prd/INIT-DS-002.md

Output: prd/reports/Resolution-INIT-DS-002.md with decisions per finding.
Do not edit PRD until I confirm resolution.
```

---

## 4 — Apply PRD fixes

**When:** Resolution report approved; update PRD and spec drafts on PR branch.

```text
/update-documents

Resolution: prd/reports/Resolution-INIT-DS-002.md
Update: prd/INIT-DS-002.md
Also align: (list spec paths on open PR branches if any)
```

---

## 5 — Spec handoff PR (product INIT — one repo)

**When:** Phase 1 — PM opens docs-only PR per app repo. **Dev merges** — PM does not merge app `develop`.  
**Branch:** `chore/INIT-<id>-spec-handoff-<repo>` from app `develop`

```text
Initiative: INIT-DS-002
Repo: example-api
Branch: chore/INIT-DS-002-spec-handoff-example-api from develop

Start from <client>-meta/templates/INIT-spec-handoff.md (wave IDs must match PRD §4.0).
Gate: playbook/spec-layout.md § INIT spec handoff.

Update docs/specification/product/ only:
- product/INIT-DS-002.md (slice for this repo)
- 02-api-contract.md deltas if routes change
- 04-cross-service-contracts.md if integrations change

No src/. No tests/.
Link meta PRD: prd/INIT-DS-002.md (meta PR branch or develop after Phase 2 merge).

Then run /validate-requirements on this branch against that PRD.
```

---

## 6 — Spec vs PRD conformance (PM only — meta workspace)

**When:** PM validates spec drafts against PRD **before** opening spec handoff PRs (or after `/update-documents`). **Not** seeded in app-repo harness.

```text
/validate-requirements

Initiative: INIT-DS-002
Primary doc: prd/INIT-DS-002.md on <client>-meta develop
Spec draft: product/INIT-DS-002.md on handoff branch (or pasted path)
Check: repo spec slice matches PRD.
Report only — list gaps; do not merge spec PR until clean.
```

**Dev spec PR review:** `/spec-feasibility-review` only — spec links Validation report; no `/validate-requirements` in app repo.

---

## 7 — Generate work manifest (after Phase 2 merges)

**When:** Meta PRD + all spec PRs merged to `develop`.  
**Output:** `work/INIT-*.yaml`

```text
/generate-work-manifest

PRD: prd/INIT-DS-002.md on <client>-meta develop
Read delivery_model from PRD §4.0 (playbook/delivery-model.md).
If delivery_model: waves — one manifest task per wave ID (W0, W1, …, PRE* from merged spec).
If delivery_model: repo-slice — one task per repo (v1).

Merged spec paths:
- example-registry docs/specification/product/INIT-DS-002.md
- (other repos)

Output: work/INIT-DS-002.yaml
apiVersion: meta.meta/v1 for example-org (see work/INIT-PARICHAY-001.yaml).
Include dry-run seed command; do not run seed-work unless I ask.
```

**Terminal (PM):** after manifest PR merges:

```bash
launchpad seed-work --config work/INIT-DS-002.yaml --dry-run
launchpad seed-work --config work/INIT-DS-002.yaml --apply
```

---

## 8 — INIT retro — spec handoff (chore closure)

**When:** PRD signed off; retro closure like **INIT-PARICHAY-001** (implementation already on `develop`).  
**One PR** per repo — dev merges; **no `src/`**.

```text
Initiative: INIT-PARICHAY-001
Repo: example-api
Branch: chore/INIT-PARICHAY-001-spec-handoff-example-api from develop

Add docs/specification/product/INIT-PARICHAY-001.md:
- Status Closed / retro; link to <client>-meta prd/INIT-PARICHAY-001.md
- As-delivered wave table (#27–#32) + dev read order
- Delete superseded product quality spec; update README + tests/README header

No src/. No tests/.

PR title: [spec] handoff — INIT-PARICHAY-001 — example-api
Label: spec
```

**PRD:** [prd/INIT-PARICHAY-001.md](../prd/INIT-PARICHAY-001.md)

---

# Developer prompts

**Workspace:** app repo root (e.g. **`example-api`**), branch `develop` (or feature branch from develop).  
**Skills:** prayog-skills dev bundle in `.agents/skills/` (seeded by `sync-harness`).  
**Do not** edit `.cursor/rules/` submodule — propose upstream in service-rules. Skill changes → [prayog-skills](https://github.com/drivestream-lab/prayog-skills).

**Read first:** `AGENTS.md` → board issue **Spec path** → `docs/specification/as-built/`.

---

## D1 — Product INIT — implementation slice

**When:** Board issue from seeded INIT epic; spec handoff already on `develop`.  
**One issue = one PR.**

```text
Initiative: INIT-DS-002
Issue: #42 — [feature] Short title from GitHub
Repo: example-api (this workspace)

/pre-implement

Read:
- AGENTS.md
- docs/specification/product/INIT-DS-002.md
- docs/specification/product/02-api-contract.md (if routes)
- docs/specification/as-built/implementation-status.md

Execute one slice:
1. Implement code + tests (unit vs verify — no overlap)
2. Update product spec status if behavior ships
3. Update as-built/implementation-status.md in same PR
4. Run board Verify command

Branch: feature/INIT-DS-002-<slug>
Verify: (paste from board — e.g. make check && poetry run python -m tests.verify.verify_all)

Do not edit .cursor/rules/ submodule.
```

---

## D2 — Test maintenance chore (post–INIT-PARICHAY-001)

**When:** Future test work on example-api after **INIT-PARICHAY-001** retro closure. Waves W1–W5 are **done** — do not re-run.  
**Handoff SSOT:** `docs/specification/product/INIT-PARICHAY-001.md`

```text
Initiative: INIT-PARICHAY-001
Issue: #<n> — [chore] <test area>
Repo: example-api (this workspace)

/pre-implement

Read:
- docs/specification/product/INIT-PARICHAY-001.md (dev read order)
- docs/specification/product/<relevant capability>.md
- docs/specification/as-built/implementation-status.md (## Testing harness)
- tests/README.md

Deliver per overlap rules: unit and/or verify trim; update feature map + as-built.

Branch: chore/INIT-PARICHAY-001-<slug>
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

## D3 — Spec PR review (dev merges PM handoff)

**When:** PM opened `[spec] handoff` PR; dev reviews before merge.  
**Workspace:** app repo, checkout spec PR branch.

### D3a — Feasibility (required)

```text
/spec-feasibility-review

Initiative: INIT-ABHILEKH-001
Spec PR branch: chore/INIT-ABHILEKH-001-spec-handoff-example-registry
Spec: docs/specification/product/INIT-ABHILEKH-001.md
PRD (optional): <client>-meta prd/INIT-ABHILEKH-001.md

Output: docs/specification/reports/Feasibility-Report-INIT-ABHILEKH-001.md
End with PM questions (blocking vs defer). No src/ in spec PR.
```

### D3b — PRD traceability (required, no extra skill)

Confirm spec header links **Meta PRD** + **Validation report** (`prd/reports/Validation-Report-*.md`). PM owns `/validate-requirements`; dev does not re-run it in the app repo.

### D3c — Implementation plan (after feasibility sign-off, post-merge or before seed)

```text
/spec-implementation-plan

Initiative: INIT-ABHILEKH-001
Feasibility: docs/specification/reports/Feasibility-Report-INIT-ABHILEKH-001.md
Spec: docs/specification/product/INIT-ABHILEKH-001.md

Output: docs/specification/reports/Implementation-Plan-INIT-ABHILEKH-001.md
```

For INIT retro handoff:

```text
Review spec PR chore/INIT-PARICHAY-001-spec-handoff-example-api:

Read docs/specification/product/INIT-PARICHAY-001.md
Check: retro narrative, as-delivered waves, QUALITY doc removed,
       dev read order clear, no src/ changes.
Approve if ready to merge to develop.
```

---

## D4 — Verify only (post-implementation)

**When:** Code done; run board verify before opening PR or after CI.

```text
/verify

Initiative: INIT-PARICHAY-001
Issue: #<n>
Verify command: make test

Run the command; report pass/fail and any fixes needed.
```

Live stack example:

```text
/verify

Initiative: INIT-DS-002
Issue: #42
Verify command: make check && poetry run python -m tests.verify.verify_all

conda activate example-api required for verify_all.
```

---

## D5 — Cross-service check

**When:** Issue touches HTTP routes, JWT claims, or peer integrations.

```text
Initiative: INIT-DS-002
Issue: #42
Repo: example-api (this workspace)

Before implementing:
Read docs/specification/product/04-cross-service-contracts.md
Read example-registry docs/specification/product/ (relevant integration doc)

Confirm example-api changes do not break EMQX auth, device validation, or Kafka bridge contracts.
```

---

## D6 — Harness / platform chore (bootstrap — reference)

**When:** BOOTSTRAP-DS-001-style harness work in app repo (historical).

```text
Initiative: BOOTSTRAP-DS-001
Repo: example-api
Task: Harness only — no product features.

/pre-implement

Deliverables: AGENTS.md links to <client>-meta playbook; .cursor/skills; PR template; as-built columns.
Verify: make check
```

---

## PR traceability (both roles)

Every PR description should match board fields:

| Field | Example |
|-------|---------|
| Initiative | `INIT-PARICHAY-001` or `INIT-DS-002` |
| Issue | `#<n>` |
| Spec path | `docs/specification/product/INIT-PARICHAY-001.md` |
| Verify command | `make test` |

Template: app repo `.github/pull_request_template.md`
