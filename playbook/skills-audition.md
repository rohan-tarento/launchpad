# Skills audition

Score skills before marking harness or PM pipeline ready. Lab sample prompts: [launchpad/skills-audition](https://github.com/drivestream-lab/launchpad/blob/develop/playbook/skills-audition.md).

**PM skills** install from [skills-matrix.md](skills-matrix.md) (`prayog-skills` + community `prd`) — not committed in git.

**Dev skills** install via `launchpad sync-harness-app --repo <name> --apply` — commit `skills-lock.json`.

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
| spec-technical-review | | | prayog-skills dev (PE lane) |
| spec-implementation-plan | | | prayog-skills dev |
| pre-implement | | | prayog-skills dev |
| loop-spec | | | prayog-skills dev |
| ground-spec | | | prayog-skills dev |
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

## 5. spec-technical-review (app repo, PE lane — after feasibility)

**When:** Feasibility report has NEW-ADR or Critical engineering findings.

```text
/spec-technical-review

Initiative: INIT-EXAMPLE-003
Feasibility report: docs/specification/reports/Feasibility-Report-INIT-EXAMPLE-003.md
```

**Pass if:** TDD produced; T1–T10 checks evidenced; draft ADRs for each NEW-ADR finding; PE questions resolved or deferred with defaults; PM questions explicitly routed (not answered by agent).

---

## 6. spec-implementation-plan (app repo, post-feasibility + PE sign-off)

```text
/spec-implementation-plan

Initiative: INIT-EXAMPLE-003
Feasibility report path: docs/specification/reports/Feasibility-Report-INIT-EXAMPLE-003.md
Technical review path: docs/specification/reports/Technical-Review-INIT-EXAMPLE-003.md
```

**Pass if:** §0 PE sign-off referenced; W0–Wn phases with REQ/TASK/FILE; done-when per task; P1–P14 checks in report; §WorkManifest YAML present.

---

## 7. loop-spec (app repo, during wave implementation)

```text
/loop-spec

Implement W1 for INIT-EXAMPLE-003. Run {verify_command} and {check_command} after each task.
Fix failures before moving on. Stop when all tasks green.
```

**Pass if:** agent implements task-by-task; verifies after each; fixes before proceeding; stops and requests human checkpoint — does not self-approve or advance to next wave.

---

## 8. ground-spec (app repo, after wave implementation)

```text
/ground-spec

Spec: 01  (or wave W1 of INIT-EXAMPLE-003)
```

**Pass if:** ground check output included; FR checklist evidenced; §Contracts produced table populated with module, entry point, input/output shapes; PR instructions present.

---

## Exit

- [ ] Dev bundle (§1–2, §4–8) scored **Y** on pilot repo
- [ ] `launchpad verify-harness-app --repo <pilot>` passes after harness migration PR
