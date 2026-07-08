# Skills matrix (example-org)

Agent skills and factory commands for Example engineering. **PM pipeline skills** install from [drivestream-lab/prayog-skills](https://github.com/drivestream-lab/prayog-skills).

**Audition:** [skills-audition.md](skills-audition.md)  
**Full workflow:** [delivery-workflow.md](delivery-workflow.md)

Skills CLI installs to **`.agents/skills/`** (project) or **`~/.agents/skills/`** (global).

**Dev + PM skills SSOT:** [prayog-skills](https://github.com/drivestream-lab/prayog-skills) @ harness pin. App repos: [`apply-harness`](harness-pins.md).

---

## Two workspaces

| Who | Open in Cursor | Skills |
|-----|----------------|--------|
| **PM / PO** | `<client>-meta` | `prd` + prayog PM bundle via `apply-harness --meta` |
| **Developer** | app repo | prayog dev bundle — `/spec-draft` through `/verify` |

---

## PM pipeline (meta — PRD PR)

| Step | Skill | Source |
|------|-------|--------|
| Draft | `prd` | Community — [awesome-copilot](https://github.com/github/awesome-copilot) |
| Audit | `validate-requirements` | prayog-skills |
| Decide | `review-findings` | prayog-skills |
| Apply | `update-documents` | prayog-skills |
| Impact map | `prd-impact-map` | prayog-skills |

Install:

```bash
launchpad apply-harness --meta --apply
launchpad check-harness --meta
```

Invoke: `/prd`, `/validate-requirements`, `/review-findings`, `/update-documents`, `/prd-impact-map`

---

## Dev pipeline (app repo — spec PR)

| Step | Skill |
|------|-------|
| Spec slice | `spec-draft` |
| Feasibility | `initiative-feasibility` |
| PE review (conditional) | `spec-technical-review` |
| Plan + §9 | `spec-implementation-plan` |
| Per wave | `pre-implement` → `loop-spec` → `ground-spec` → `verify` |

```text
Eng opens spec PR (chore/INIT-{COMPONENT}-{NUMBER}-spec-<repo>)
  → /spec-draft → /initiative-feasibility
  → /spec-technical-review (if NEW-ADR) — PE Approve on same spec PR
  → /spec-implementation-plan — plan + §9 on spec branch
  → merge spec PR
  → gh issue create per wave from §9
  → /pre-implement → /loop-spec → /ground-spec → feature PR
```

Harness: `launchpad apply-harness --repo <name> --apply` — see [harness-pins.md](harness-pins.md).

---

## PRD refinement loop

```text
/prd → /validate-requirements → /review-findings → /update-documents → /validate-requirements (incremental)
```

Detail: [delivery-workflow.md](delivery-workflow.md) · [pm-workflow.md](pm-workflow.md)

---

## Related

- [agent-prompt-templates.md](agent-prompt-templates.md)
- [github-project.md](github-project.md)
