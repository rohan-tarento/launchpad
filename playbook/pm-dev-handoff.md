# PM ↔ dev handoff (example-org)

How product intent moves from **<client>-meta** into service repos before implementation. Enforced by **teams + branch protection** — see [teams-and-rbac.md](teams-and-rbac.md) and [github-enforcement.md](github-enforcement.md).

**Skills:** PRD pipeline and conformance gate — [skills-matrix.md](skills-matrix.md).

---

## Mental model

| Layer | Repo | Who merges `develop` | Contents |
|-------|------|----------------------|----------|
| **Initiative** | `<client>-meta` | **`pm-team`** | Work manifests, playbook, validation reports (PRD when INIT exists) |
| **Repo slice** | each app repo | **Profile dev team** | Spec deltas + `02-api-contract` (+ integrations when multi-service) |
| **Implementation** | each app repo | **Profile dev team** | Code, verify, `as-built` |

PM has **Write on all repos** (push handoff branches). PM **does not merge** app-repo `develop`. Devs have **Read on meta** (PRD only).

---

## Truth hierarchy

| Document | Owner after handoff |
|----------|---------------------|
| `<client>-meta/work/INIT-*.yaml` | PM (via manifest PR) |
| `<client>-meta/playbook/` | PM / platform |
| `docs/specification/product/` | Dev (PM may draft in handoff PR) |
| `docs/specification/as-built/implementation-status.md` | Dev only |

When a product PRD exists: **meta PR first** → spec handoff PR per app repo → then implementation.

---

## Sprint timeline (three phases)

### Phase 1 — Open PRs, iterate, **do not merge**

Run while PRD or specs may still change. Devs review without locking `develop`.

```text
PM: meta PR → develop          (playbook + work manifest) — open, NOT merged
PM: prd-handoff PR per repo   (PRD link + plain-English scope; no spec files from PM) — open, NOT merged
Dev: read meta PR branch or PR diff for PRD (develop PRD is stale until Phase 2)
Dev: read PRD from PR branch → run `/spec-draft` → write spec slice → run `/initiative-feasibility`
PM + dev: push fixes to same PRs until aligned
```

**How dev gets PRD during iteration:** checkout meta PR branch, GitHub PR “Files changed”, or local multi-repo with meta on handoff branch. Do not rely on `develop` PRD until Phase 2. Spec header must link **Meta PRD** + **Validation report** — dev reads those; dev harness does **not** include `/validate-requirements`.

**PRD conformance (PM only):** PM runs `/validate-requirements` on the PRD (and spec drafts on handoff branches) in **<client>-meta** before Phase 2 merge. Devs do not re-run it in app repos.

Link every spec PR to the meta PR URL in the description.

### Phase 2 — Coordinated merge (alignment gate)

Only when iteration is complete on **all** linked PRs:

```text
1. PM merges meta PR → <client>-meta/develop     (PRD + process docs land)
2. Dev merges spec PRs → each app develop      (merge order: example-api → example-registry → ops → compose)
```

PM merges meta **first** (or same session) so `develop` PRD is the baseline for traceability; spec PRs should already match the final meta PR branch.

### Phase 3 — Backlog, then implementation

**After both meta and spec PRs are merged** — not before:

```text
Dev: /spec-implementation-plan → §WorkManifest YAML
Dev: gh issue create (single repo) OR launchpad seed-work (multi-repo) → epic + issues on Project
Dev: feature/INIT-{COMPONENT}-{NUMBER}-w{N}-{slug} from develop → implement → PR → develop
```

Epic/tasks reference **merged** `prd/INIT-*.md` and repo `INIT-*.md` on `develop`, not draft PR branches.

**Delivery model:** See [delivery-model.md](delivery-model.md). When PRD `delivery_model: waves`, manifest issues **must mirror** PRD/spec wave IDs (W0, W1, …, PRE*). One wave = one board issue = one PR.

---

Merge order for INIT features: **example-api → example-registry → ops** (compose seed can run in parallel with example-api).

---

## PR types

### Meta PR (PM merges)

| Item | Detail |
|------|--------|
| **Branch** | `chore/INIT-*-prd` or `chore/INIT-*-meta` from `develop` |
| **Target** | `<client>-meta` → `develop` |
| **Files** | `work/*.yaml`, playbook updates, reports |
| **Merge** | **`pm-team` only** (branch protection) |

### Spec handoff PR (dev merges)

| Item | Detail |
|------|--------|
| **Branch** | `chore/INIT-*-spec-handoff-<repo>` from `develop` |
| **Target** | app repo → `develop` |
| **Files** | `INIT-*.md`, `02-*` / `02-route-map`, `03-integrations` — **no product code** |
| **Label** | `spec` |
| **Merge** | **Profile dev team only** (`backend-devs`, `frontend-devs`, `platform-devs`) |
| **Gate** | [Conformance](skills-matrix.md#spec-conformance-gate-per-repo--after-prd-sign-off) clean on PR before merge |

### Implementation PR (dev merges)

| Item | Detail |
|------|--------|
| **Branch** | `feature/INIT-*-<slug>` from `develop` |
| **Files** | Code + spec status updates + `as-built` |
| **Merge** | Profile dev team |

---

## Closed initiatives (example — do not re-open)

| Initiative | Status | SSOT |
|------------|--------|------|
| **INIT-EXAMPLE-001** | Documentation / smoke only | [work/INIT-EXAMPLE-001.yaml](../examples/tenant-meta/work/INIT-EXAMPLE-001.yaml) |

New work uses **`INIT-<scope>-<nnn>`** only ([pm-workflow.md](pm-workflow.md)).

---

## Product INIT (standard pipeline)

| Repo | Handoff files | Verify (example) |
|------|---------------|------------------|
| **example-api** | `INIT-*.md`, `02-api-contract.md`, cross-service docs | `poetry run python -m tests.verify.verify_all` |
| **example-registry** | same pattern | per `tests/README.md` |
| **example-bff** | `INIT-*.md`, `02-route-map.md` | per repo README |

---

## Checklists

### PM — before spec handoff PR

- [ ] PRD validation clean ([skills-matrix](skills-matrix.md) PRD loop)
- [ ] Branch from latest `develop`
- [ ] One PR per app repo (+ meta PRD PR)
- [ ] PR title: `[spec] handoff — INIT-… — <repo>`
- [ ] Link meta PRD path in PR description

### Dev — on prd-handoff PR branch (Phase 1)

- [ ] Read PRD from meta PR branch; confirm scope for this repo with PM
- [ ] Run `/spec-draft` — generate spec slice into `docs/specification/product/`
- [ ] Review + edit spec slice; confirm it matches prd-handoff PR scope
- [ ] Run `/initiative-feasibility` — save report under `docs/specification/reports/`
  ([skills-audition §4](skills-audition.md))
- [ ] Post PM questions as PR comments on prd-handoff PR (plain English)
- [ ] **Wave parity:** spec `delivery_model` and wave IDs match PRD §4.0
  ([delivery-model.md](delivery-model.md))

### Dev — after Phase 2 merge (spec + PRD on develop)

- [ ] Run `/spec-technical-review` when feasibility has PE-lane (NEW-ADR) findings —
  TDD + draft ADRs; PE approves
- [ ] Run `/spec-implementation-plan` — wave-level plan + §WorkManifest YAML
- [ ] Seed board: `gh issue create` (single repo) or `launchpad seed-work` (multi-repo)

### PM — Phase 2 merge

- [ ] All PM questions on prd-handoff PRs answered / resolved
- [ ] **Merge meta PR first** → `<client>-meta/develop`
- [ ] Confirm dev merges prd-handoff PRs (PM does not merge app repos)

### Dev — implementation (per wave)

- [ ] Open `feature/{sc}-w{N}-{slug}` from `develop` (see [branching-policy.md](branching-policy.md) for `{sc}` short-code rule)
- [ ] `/pre-implement` — gate check: prior wave `human_approved`; confirm contracts from prior ground report
- [ ] Implement → `/loop-spec` until green
- [ ] `/ground-spec` — commit Ground Report as last commit on same branch; update `as-built` to `grounded`
- [ ] Open PR — ground report is part of the PR (not a separate PR)
- [ ] Required reviewer (`@dev-leads` via CODEOWNERS) approves → merge → `as-built` = `human_approved`
- [ ] PR traceability block ([sdd-workflow.md](sdd-workflow.md))

---

## Sign-off workflow (GitHub-first)

Every skill gate is a merged PR with required reviewer approval.
Approval by silence is forbidden — reviewer must give explicit GitHub Approve or Request Changes.
If no response by deadline: escalate — do not proceed and do not assume approval.

| Artifact | Branch | PR title | Required reviewer | Deadline |
|----------|--------|----------|-------------------|----------|
| Feasibility report | `chore/{sc}-feasibility` | `[{sc}] Feasibility — {N} blocking items` | PM + Domain SME | 3 business days |
| Technical Design Doc | `chore/{sc}-technical-review` | `[{sc}] TDD — PE review required` | `@pe-team` (CODEOWNERS) | 5 business days |
| Implementation plan | `chore/{sc}-plan` | `[{sc}] Implementation plan — team review` | `@dev-leads` | 3 business days |
| Wave W{N} + ground report | `feature/{sc}-w{N}-{slug}` | `[{sc} W{N}] {slug}` | `@dev-leads` (CODEOWNERS) | 2 business days |

CODEOWNERS template: ``launchpad/templates/CODEOWNERS.backend` (or profile variant)` — copy to each repo on bootstrap.
Branch protection required: **"Require review from Code Owners"** on `develop`.

---

## GitHub setup

```bash
launchpad bootstrap-teams --config config/org-example.yaml --apply
launchpad setup-gitflow --org example-org --apply
```

Add people to **`pm-team`** and dev teams in GitHub → Organization → Teams.

Config: [`examples/tenant-meta/config/gitflow-example.yaml`](../examples/tenant-meta/config/gitflow-example.yaml)

---

## Related

- [branching-policy.md](branching-policy.md) — branch naming
- [sdd-workflow.md](sdd-workflow.md) — SDD read order in each repo
- [exit-criteria.md](exit-criteria.md) — bootstrap closure
