# PM workflow (Cursor + meta)

How **PM / product owner** runs the product lane in **<client>-meta**. Skills are **installed via CLI** from lab-proven packages — see [skills-matrix.md](skills-matrix.md). Merge rules: [pm-dev-handoff.md](pm-dev-handoff.md).

**Workspace:** open **`<client>-meta`** in Cursor (not app repos).

**Board:** [Example Engineering](https://github.com/orgs/example-org/projects/1)

---

## One-time setup (PM machine)

From `<client>-meta` root:

```bash
npx skills add github/awesome-copilot --skill prd -a cursor -y
npx skills add drivestream-lab/prayog-skills --skill '*' -a cursor -y
npx skills list
```

Do **not** expect PM skills under `.cursor/skills/` in git — they live in `.agents/skills/` locally (gitignored pattern per skills-matrix).

---

## Skills by phase

| Phase | Invoke | Output |
|-------|--------|--------|
| Draft | `/prd` | `prd/INIT-<id>.md` |
| Audit | `/validate-requirements` | `prd/reports/Validation-Report-*.md` |
| Decide | `/review-findings` | `prd/reports/Resolution-*.md` |
| Apply | `/update-documents` | Updated PRD + spec drafts on PR branch |
| Spec vs PRD (PM) | `/validate-requirements` | Clean Validation report before handoff |
| Backlog | `/generate-work-manifest` | `work/INIT-<id>.yaml` |
| Board | `launchpad seed-work` | GitHub issues (terminal) |

**Developers** (app repos, harness dev bundle): `/spec-feasibility-review`, `/spec-implementation-plan`, `/pre-implement`, `/verify` — **not** `/validate-requirements`.

---

## Three phases (same as pm-dev-handoff)

### Phase 1 — Open PRs, iterate, **do not merge**

```text
PM: chore/INIT-*-prd on meta → /prd loop
PM: chore/INIT-*-spec-handoff-<repo> on each app repo (docs only)
Dev: review spec PRs; /spec-feasibility-review on spec PR branches
PM + dev: /review-findings → /update-documents until clean
```

### Phase 2 — Coordinated merge

```text
1. PM merges meta PR → <client>-meta/develop
2. Dev merges spec PRs → each app develop (example-api → peers)
```

### Phase 3 — Backlog + implementation

```text
/generate-work-manifest → work/INIT-*.yaml PR   (reads PRD delivery_model — see delivery-model.md)
launchpad seed-work --apply
Dev picks board issues → /pre-implement → code → /verify → PR
```

**Gate:** `seed-work` only after Phase 2 — issues cite **merged** paths on `develop`.

**Waves:** When PRD `delivery_model: waves`, board has one issue per wave (W0…Wn); dev implements in order.

---

## Example prompts

Copy-paste templates with **PM** and **Developer** sections: [agent-prompt-templates.md](agent-prompt-templates.md)

| Role | Section |
|------|---------|
| Product owner / PM | Prompts **1–8** (meta workspace) |
| Developer | Prompts **D1–D6** (app repo — example-api examples include QUALITY #28) |

---

## Talking about tickets

Use **GitHub issue #** and **full issue title** on the board. Manifest ids (`Q1`, `T2`) are for `depends_on` in YAML only.

---

## Chore vs product

| Type | Example | PM path |
|------|---------|---------|
| Bootstrap | BOOTSTRAP-001 | Factory + playbook |
| Retro closure | INIT-EXAMPLE-001 | PRD + spec handoff; optional `seed-work` |
| Product | INIT-* | Full pipeline above |

---

## Related

- [skills-matrix.md](skills-matrix.md) — install commands
- [skills-audition.md](skills-audition.md) — sample runs
- [wiki: PM workflow](../wiki/PM-workflow.md)
