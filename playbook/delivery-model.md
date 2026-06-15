# Delivery model (INIT initiatives)

How implementation work is **declared** (PRD), **detailed** (repo spec), **tracked** (board), and **accepted** (PR merges).

**SSOT chain:**

```text
PRD delivery_model + wave table
  → repo spec (mirror wave IDs; may add PRE* gates)
  → work manifest (one issue per delivery unit)
  → seed-work → GitHub Project
  → feature branch PR per wave → merge → wave Done
  → INIT closure when all units + success criteria pass
```

Related: [pm-dev-handoff.md](pm-dev-handoff.md) · [spec-layout.md](spec-layout.md) · [pm-workflow.md](pm-workflow.md)

---

## Delivery models

Every INIT PRD declares exactly one model:

| Model | When to use | Board shape |
|-------|-------------|-------------|
| **`waves`** | Single-repo or harness INITs with phased delivery; test-quality programs; any PRD with an implementation wave table | Epic + **one issue per wave** (W0…Wn, optional PRE*) |
| **`repo-slice`** | Multi-repo product INIT where each app repo merges one implementation slice | Epic + **one issue per repo** |

**Default for harness / tech-debt INITs:** `waves`.

---

## 1:1 rule (waves model)

| Unit | Artifact |
|------|----------|
| 1 wave ID (e.g. **W2**) | 1 board issue |
| 1 board issue | 1 feature PR |
| 1 feature PR | 1 merge to `develop` |
| Wave **Done** | Per-wave PR gate passed (not whole INIT) |

Manifest task `id` **must equal** PRD/spec wave id (`W0`, `W1`, `PRE1`, …).

---

## Wave naming

| ID | Role |
|----|------|
| **W0** | Structure only — layout, CI, docs skeleton (no domain unit tests beyond health move) |
| **W1–Wn** | Domain — unit tests + verify alignment per wave table |
| **PRE*** | Optional plan/doc gate before a wave (e.g. unit test case matrix before W1) |

**Branch:** `feature/INIT-<id>-w<N>-<kebab-slug>`  
**Issue title:** `[W<N>] <short summary>` or `[PRE1] <gate name>`

Do **not** use legacy labels (`4a`, `Phase 4b`) in new INITs — use **W0–Wn** only.

---

## Acceptance levels

### Per-wave (merge gate)

Blocked until all pass (from PRD/spec):

- Feature-map / as-built rows for touched capabilities updated (same PR)
- `make check && make test` green
- Overlap audit — no full HTTP journey duplicated in pytest
- Verify module headers updated where applicable

### INIT closure

After **all** wave issues are Done:

- Meta PRD success criteria (S1–Sn)
- Live verify / harness verify per PRD (closure gates — not necessarily every wave in CI)
- Board epic closed
- [pm-dev-handoff.md](pm-dev-handoff.md) Phase 3 checklist complete

---

## Responsibilities

| Step | PM | Dev |
|------|-----|-----|
| Declare `delivery_model` + waves in PRD | ✓ | review |
| Draft spec from [templates/INIT-spec-handoff.md](../templates/INIT-spec-handoff.md) | ✓ draft | ✓ merge |
| `generate-work-manifest` (prayog-skills) | ✓ | — |
| `seed-work` | ✓ | — |
| Implement wave PRs | — | ✓ |
| Close epic | ✓ | verify S-criteria |

---

## Manifest skill behavior

`/generate-work-manifest` (prayog-skills) reads PRD `delivery_model`:

| PRD | Manifest |
|-----|----------|
| `waves` | Epic + one `work[]` item per wave (+ PRE* from merged spec) |
| `repo-slice` | Epic + one task per repo ([v1-granularity](https://github.com/drivestream-lab/prayog-skills)) |

Do not hand-write wave manifests when the skill can read merged PRD + spec on `develop`.

---

## Agent templates (meta)

| Template | Use |
|----------|-----|
| [templates/INIT-PRD-outline.md](../templates/INIT-PRD-outline.md) | `/prd` — Delivery section stub |
| [templates/INIT-spec-handoff.md](../templates/INIT-spec-handoff.md) | Spec handoff PR on app repo |

Playbook = policy; templates = agent starting structure.
