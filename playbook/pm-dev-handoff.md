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
PM: spec handoff PR per repo   (INIT + 02 + 03) — open, NOT merged
Dev: read meta PR branch or PR diff for PRD (develop PRD is stale until Phase 2)
Dev: review spec PRs — `/spec-feasibility-review`, comments, co-edit on PR branches
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
PM: generate-work-manifest → work/INIT-*.yaml (PR review)
PM: seed-work --dry-run → --apply → epic + issues on Project (cite merged paths on develop)
Dev: feature/INIT-* from develop → implement → PR → develop
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

### Dev — spec PR review

- [ ] Confirm spec links **Meta PRD** + **Validation report** (PM-owned `/validate-requirements` output)
- [ ] **Wave parity:** spec `delivery_model` and wave IDs match PRD §4.0 / §4.5 ([delivery-model.md](delivery-model.md))
- [ ] Run `/spec-feasibility-review` — save report under `docs/specification/reports/` ([skills-audition §4](skills-audition.md))
- [ ] Resolve PM questions on PR; approve + **merge** (PM cannot merge app `develop`)

### Dev — after spec merge (before or with seed)

- [ ] Run `/spec-implementation-plan` — wave-level plan in `docs/specification/reports/` ([skills-audition §5](skills-audition.md))

### PM — Phase 2 merge

- [ ] All spec PRs approved / conformance clean
- [ ] **Merge meta PR first** → `<client>-meta/develop`
- [ ] Confirm dev merges spec PRs (PM does not merge app repos)

### PM — Phase 3 (after all merges)

- [ ] Cross-service pass on meta ([skills-audition §7d](skills-audition.md#7-spec-conformance-gate-per-repo))
- [ ] `generate-work-manifest` (prayog-skills) → `work/INIT-*.yaml` PR merged — wave IDs match PRD/spec when `delivery_model: waves`
- [ ] `seed-work` / epic + issues on Project ([github-project.md](github-project.md))
- [ ] Issues cite **merged** `prd/INIT-*.md` + repo `INIT-*.md` + verify command
- [ ] Reinstall prayog-skills after upstream manifest skill updates ([skills-matrix](skills-matrix.md))

### Dev — implementation

- [ ] `feature/INIT-*` from `develop`
- [ ] Update `as-built` in same PR as code
- [ ] PR traceability block ([sdd-workflow.md](sdd-workflow.md))

---

## GitHub setup

```bash
launchpad bootstrap-teams --config config/org-example-org.yaml --apply
launchpad setup-gitflow --org example-org --apply
```

Add people to **`pm-team`** and dev teams in GitHub → Organization → Teams.

Config: [`examples/tenant-meta/config/gitflow-example.yaml`](../examples/tenant-meta/config/gitflow-example.yaml)

---

## Related

- [branching-policy.md](branching-policy.md) — branch naming
- [sdd-workflow.md](sdd-workflow.md) — SDD read order in each repo
- [exit-criteria.md](exit-criteria.md) — bootstrap closure
