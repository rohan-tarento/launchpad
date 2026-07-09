# Delivery workflow

How an initiative moves from PRD to shipped code. **Start here.**

Skills define *what runs* ([prayog-skills](https://github.com/drivestream-lab/prayog-skills)). This document defines *where* — which repo, which PR, who merges, and when.

**Related:** [delivery-model.md](delivery-model.md) · [skills-matrix.md](skills-matrix.md) · [branching-policy.md](branching-policy.md) · [teams-and-rbac.md](teams-and-rbac.md)

---

## Two repos, two PRs

```text
META (<client>-meta)                    APP (example-api, …)
────────────────────                    ────────────────────

PRD PR  (PM opens, PM merges)           SPEC PR  (ENG opens, ENG merges)
branch: chore/INIT-*-prd                branch: chore/INIT-*-spec-<repo>

Skills 1–5                              Skills 7–10 (while PR open)
  product Q&A HERE                        engineering Q&A HERE
  impact map LGTM                         spec + feasibility + TDD + plan
        │                                         │
        │  parallel OK after impact LGTM          │
        └─────────────────────────────────────────┘
                          │
              spec PR merge = ready to build
                          │
                          ▼
                   board seed (gh issue create)
                          │
                          ▼
                   skills 12–15 per wave
```

**PM never writes spec files. Dev never writes PRD files. PM never authors `work/INIT-*.yaml` for product INITs.**

---

## Mental model (RBAC)

| Layer | Repo | Who merges `develop` | Contents |
|-------|------|----------------------|----------|
| **Initiative** | `<client>-meta` | **`pm-team`** | PRD, validation reports, playbook updates |
| **Repo slice** | each app repo | **Profile dev team** | Spec, feasibility, TDD, plan, `02-api-contract` |
| **Implementation** | each app repo | **Profile dev team** | Code, verify, `as-built` |

PM has **Write on all repos** but **does not merge** app-repo `develop`. Devs have **Read on meta** (PRD only).

---

## Skill chain — execution order

### PM phase (`<client>-meta` workspace)

| Step | Skill | Output | PR surface |
|------|-------|--------|------------|
| 1 | `/prd` | `prd/INIT-*.md` | PRD PR |
| 2 | `/validate-requirements` | validation report | PRD PR |
| 3 | `/review-findings` | resolution report | PRD PR |
| 4 | `/update-documents` | refined PRD | PRD PR |
| 5 | `/prd-impact-map` | impact map comment | PRD PR → **tech lead LGTM** |

### Dev phase (app repo workspace)

| Step | Skill | Output | When |
|------|-------|--------|------|
| 6 | *(eng opens spec PR)* | branch `chore/INIT-*-spec-<repo>` | After impact map LGTM; may parallel open PRD PR |
| 7 | `/spec-draft` | `product/INIT-*.md`, `02-api-contract.md` | Spec PR open |
| 8 | `/initiative-feasibility` | feasibility report + 4-lane triage | Spec PR open |
| 9 | `/spec-technical-review` | TDD + draft ADRs — **conditional** (NEW-ADR) | Spec PR open; PE Approve on **same spec PR** |
| 10 | `/spec-implementation-plan` | plan + §9 WorkManifest YAML | Spec PR open; **before spec merge** |
| 11 | *(board seed)* | `gh issue create` per wave | **After spec PR merge only** |

### Wave loop (per wave W0 → Wn)

| Step | Skill | Output |
|------|-------|--------|
| 12 | `/pre-implement` | pre-flight checklist |
| 13 | `/loop-spec` | implementation until green |
| 14 | `/ground-spec` | ground report + §Contracts produced |
| 15 | *(human gate)* | tech lead approves wave PR → `as-built` = `human_approved` |

---

## Q&A routing

| Lane | Ask on | Answered by | Blocks |
|------|--------|-------------|--------|
| **Product** — scope, UX, priority | **Meta PRD PR** | PM | Spec merge if blocking |
| **Engineering / PE** — ADR, architecture, test policy | **App spec PR** | PE / senior eng | Plan skill / spec merge |
| **Domain** — business source-of-truth | Meta PRD PR or issue | Domain SME | Spec merge if blocking |
| **Impact map** | Meta PRD PR comment | Tech lead | Eng opening spec PR |
| **Auto-fix** — naming drift | Spec branch commit | Dev / agent | Nothing |

Do **not** route engineering decisions to PM. Do **not** route product scope questions only on the spec PR — use meta PRD PR.

---

## Merge gates

| Gate | Owner | Done when |
|------|-------|-----------|
| **Impact map** | Tech lead | LGTM on meta PRD PR |
| **PRD PR merge** | PM team | Skills 1–5 clean; blocking product Q&A resolved |
| **Spec PR merge** | Eng | Spec + feasibility + TDD (if needed) + plan on branch; PE Approve if TDD present; dev lead Approve |
| **Post-merge** | Eng | Board seed from plan §9 → wave coding |

Spec PR merge means: **requirements clear, engineering ready to build.** Feasibility and planning complete **while spec PR is open** — not after merge.

---

## Work manifest

| Question | Answer |
|----------|--------|
| Who **writes** wave manifest content? | **Dev** — `/spec-implementation-plan` §9 on spec branch |
| Who **merges** `work/INIT-*.yaml` into meta? | **PM** — only if dev uses optional multi-repo bulk path (`launchpad seed-work`) |
| Is manifest required **before spec merge**? | **No** |
| When is board seeded? | **After spec PR merge** — `gh issue create` per wave from §9 |

See [delivery-model.md](delivery-model.md).

---

## PR types

### Meta PR — PRD (PM merges)

| Item | Detail |
|------|--------|
| **Branch** | `chore/INIT-*-prd` or `chore/INIT-*-meta` from `develop` |
| **Target** | `<client>-meta` → `develop` |
| **Files** | `prd/INIT-*.md`, validation reports, playbook updates |
| **Must not include** | `work/INIT-*.yaml` |
| **Merge** | **`pm-team` only** |

### App PR — spec (eng merges)

| Item | Detail |
|------|--------|
| **Branch** | `chore/INIT-*-spec-<repo>` from `develop` |
| **Target** | app repo → `develop` |
| **Eng opens with** | Link to meta PRD PR; scope for this repo from impact map |
| **Eng adds** | spec slice, feasibility report, TDD (if needed), plan — **no product code** |
| **Label** | `spec` |
| **Merge** | **Profile dev team only** |

### Meta PR — work manifest (optional, post-spec-merge)

Only when dev uses multi-repo bulk seeding: copy §9 YAML → `work/INIT-*.yaml`; PM may merge in meta before `launchpad seed-work --apply`.

### Implementation PR (dev merges)

| Item | Detail |
|------|--------|
| **Branch** | `feature/INIT-*-w{N}-<slug>` from `develop` |
| **Files** | Code + spec status + `as-built` |
| **Merge** | Profile dev team |

---

## Checklists

### PM — before / during PRD PR

- [ ] PRD validation clean ([skills-matrix](skills-matrix.md) PRD loop)
- [ ] `/prd-impact-map` run; tech lead explicit LGTM on PRD PR
- [ ] **PRD PR only** — no `work/INIT-*.yaml`
- [ ] Answer blocking product questions from eng on **this PR**

### Eng — open spec PR (may parallel PRD PR)

- [ ] Impact map tech-lead LGTM received
- [ ] Branch `chore/INIT-{COMPONENT}-{NUMBER}-spec-<repo>` from `develop`
- [ ] PR links meta PRD PR URL
- [ ] PR title: `[INIT-…] Spec — <repo>`

### Eng — while spec PR is open

- [ ] Read PRD from meta PR branch or merged develop
- [ ] Run `/spec-draft` → review/edit spec slice
- [ ] Run `/initiative-feasibility` — report on spec branch
- [ ] Post product questions on **meta PRD PR** (not spec PR)
- [ ] If NEW-ADR: run `/spec-technical-review` → commit TDD → PE Approve on **spec PR**
- [ ] Run `/spec-implementation-plan` → commit plan + §9 on spec branch
- [ ] Wave parity: spec `delivery_model` and wave IDs match PRD §4.0 ([delivery-model](delivery-model.md))

### Eng — spec PR merge gate

- [ ] All blocking PM questions answered on meta PRD PR
- [ ] All blocking domain clarifications recorded
- [ ] Feasibility re-run clean if spec/PRD changed materially
- [ ] PE Approve on spec PR when TDD present
- [ ] Dev lead Approve → merge spec PR

### Eng — after spec PR merge

- [ ] Seed board: `gh issue create` per wave from plan §9 (single repo)
- [ ] Optional multi-repo: copy §9 → `work/INIT-*.yaml` → `launchpad seed-work`

### Eng — per wave

- [ ] Branch `feature/INIT-{COMPONENT}-{NUMBER}-w{N}-{slug}` from `develop`
- [ ] `/pre-implement` → `/loop-spec` until green
- [ ] `/ground-spec` — ground report last commit on wave branch
- [ ] Open wave PR → `@dev-leads` approves → merge → `as-built` = `human_approved`

### PM — PRD PR merge

- [ ] `/validate-requirements` clean if specs changed in meta workspace
- [ ] Merge PRD PR → `<client>-meta/develop`
- [ ] PM does **not** merge app spec PRs

---

## Sign-off workflow (GitHub-first)

Every skill gate uses explicit GitHub Approve — not approval by silence.

| Artifact | Branch | Required reviewer | Deadline |
|----------|--------|-------------------|----------|
| Spec + feasibility + TDD + plan | `chore/INIT-*-spec-<repo>` | `@pe-team` (when TDD present) · `@dev-leads` | 5 / 3 business days |
| Wave W{N} + ground report | `feature/INIT-*-w{N}-{slug}` | `@dev-leads` | 2 business days |

CODEOWNERS: `launchpad/templates/CODEOWNERS.backend` (or profile variant). Branch protection: **Require review from Code Owners** on `develop`.

---

## Ship criteria

| Gate | Done when |
|------|-----------|
| PRD | Validation clean; impact map LGTM; product Q&A resolved |
| Spec pipeline | Spec PR merged (spec + feasibility + TDD + plan on `develop`) |
| Board | Issues created per wave from §9 |
| Each wave | Wave PR merged; `as-built` W{N} = `human_approved` |
| INIT | All waves approved; live verify passes; PM closes epic |

---

## Automation phases

Incremental automation via `anthropics/claude-code-action` (BYOK). Start manual; enable phases as output quality is proven.

### Day 1 — fully manual

All steps run by a human in Cursor.

### Phase A — read-only (safe first)

| Step | Trigger | Action |
|------|---------|--------|
| `/prd-impact-map` | meta PRD PR opened | Posts impact map comment |
| `/initiative-feasibility` | `@claude` on spec PR | Posts feasibility + triage |
| `/pre-implement` | Wave issue labeled `in-progress` | Posts checklist comment |

### Phase B — doc commits

| Step | Trigger | Action |
|------|---------|--------|
| `/spec-draft` | Push to `chore/INIT-*-spec-*` | Writes spec slice |
| `/spec-implementation-plan` | PE Approve on spec PR | Writes plan + §9 |
| Board seed | Spec PR merged | `gh issue create` per wave |
| `/ground-spec` | `@claude` on wave PR | Ground report commit |

### Phase C — code automation

| Step | Trigger | Action |
|------|---------|--------|
| `/loop-spec` | Pre-implement + `go-ahead` label | Implement loop; opens wave PR |

### Always human

PRD authorship, PM findings decisions, PM product answers, domain SME, PE Approve, tech lead wave review, INIT closure.

---

## Truth hierarchy

| Document | Owner |
|----------|-------|
| `<client>-meta/prd/INIT-*.md` | PM |
| `<client>-meta/work/INIT-*.yaml` | Dev generates §9; PM merges file only for bulk path |
| `docs/specification/product/` | Dev |
| `docs/specification/as-built/` | Dev only |

---

## GitHub setup

```bash
launchpad init-client --config config/governance-example-org.yaml --apply
launchpad init-client --org example-org --apply
```

Config: [`examples/tenant-meta/config/governance-example-org.yaml`](../examples/tenant-meta/config/governance-example-org.yaml)

---

## Tenant customisation

Kit default. For org deltas, add `delivery-workflow-{org}.md` under tenant `playbook/` — document differences only.
