# Skills audition

Score skills before marking harness or PM pipeline ready. Lab sample prompts: [launchpad/skills-audition](https://github.com/drivestream-lab/launchpad/blob/develop/playbook/skills-audition.md).

**PM skills** install from [skills-matrix.md](skills-matrix.md) (`prayog-skills` + community `prd`) — not committed in git.

**Dev skills** install via `launchpad sync-harness --repo <name> --apply` — commit `skills-lock.json`.

---

## Scorecard

| Skill | Sample run date | Pass (Y/N) | Notes |
|-------|-----------------|------------|-------|
| prd | | | Community awesome-copilot |
| validate-requirements | | | prayog-skills |
| review-findings | | | prayog-skills |
| update-documents | | | prayog-skills |
| generate-work-manifest | | | prayog-skills |
| spec-feasibility-review | | | prayog-skills dev |
| spec-implementation-plan | | | prayog-skills dev |
| pre-implement | | | prayog-skills dev |
| verify | | | prayog-skills dev |

---

## 1. pre-implement (app repo)

**Workspace:** app repo on `develop` after harness sync

```text
/pre-implement

Slice: one board issue / wave from initiative spec.
```

**Pass if:** checklist lists AGENTS.md, relevant `.mdc`, as-built columns; states verify vs unit scope; no code unless asked.

---

## 2. verify (app repo)

**Workspace:** app repo — server running, `tests/config.yaml` configured

```text
/verify

Run verify for one feature area per tests/README.md.
```

**Pass if:** agent cites `tests/README.md`, uses documented verify command, notes env prerequisites.

---

## 3. seed-work (operator — not a skill)

```bash
launchpad seed-work --config work/INIT-<id>.yaml --dry-run
```

**Pass if:** epic + tasks match manifest; board fields populated after apply.

---

## 4. spec-feasibility-review (app repo, spec PR branch)

**Workspace:** example-registry (or pilot repo), spec handoff branch

```text
/spec-feasibility-review

Initiative: INIT-EXAMPLE-003
Spec: docs/specification/product/INIT-EXAMPLE-003.md
```

**Pass if:** report saved; F-checks evidenced; PM questions numbered; no `src/` edits.

---

## 5. spec-implementation-plan (app repo, post-feasibility)

```text
/spec-implementation-plan

Initiative: INIT-EXAMPLE-003
Feasibility report path: docs/specification/reports/Feasibility-Report-INIT-EXAMPLE-003.md
```

**Pass if:** W0–Wn phases with REQ/TASK/FILE; done-when per task; P-checks in report.

---

## Exit

- [ ] Dev bundle (§1–2, §4–5) scored **Y** on pilot repo
- [ ] `launchpad verify-harness --repo <pilot>` passes after harness migration PR
