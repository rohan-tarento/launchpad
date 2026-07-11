# Delivery workflow integration

Launchpad supplies repository, role, GitHub, pinning, and factory bindings for
the delivery workflow installed from Prayog.

## Workflow source of truth

The normative stage graph is the pinned Prayog file:

```text
.agents/skills/prayog-skills/workflow.yaml
```

Its contract is recorded in:

```text
.harness-pin.yaml
.agents/skills/prayog-skills/delivery-contract.yaml
```

Do not copy skill transitions, checks, or output schemas into this playbook.
When asked “what next?”, agents read the latest persistent handoff and the
pinned workflow.

## Repository and role bindings

| Surface | Owner | Purpose |
|---------|-------|---------|
| `<client>-meta` PRD PR | PM team | Product clarification, PRD, impact map, Gate 1 |
| App spec PR | Profile developer team | Repo spec, feasibility, optional TDD, plan, Gate 2 |
| App wave PR | Profile developer team | Code, tests, verify evidence, ground report |
| Gate 1 | PE / tech lead | Engineering handoff readiness |
| Gate 2 | PE / engineering gate | Coding readiness |
| Wave checkpoint | Peer/tech lead | Grounded implementation evidence |

PM owns product decisions and PRD artifacts. Developers own app specs and code.
PE owns engineering decisions; PE does not choose product behavior.

## GitHub surfaces

### PRD PR

- Branch: `chore/INIT-{COMPONENT}-{NUMBER}-prd`
- Target: `develop`
- Initial impact map is generated locally before the PR exists.
- PR creation/update requires explicit user authorization.
- Product/domain clarification happens on this PR.
- Decisions are committed into PRD/map artifacts before threads resolve.
- Gate 1 labels: `impact-map-pending`, `impact-map-blocked`,
  `impact-map-lgtm`; `impact-map-revised` or `impact-map-stale` closes the gate.
- Labels are projections; matching review/head/artifact evidence remains
  authoritative.
- Pilot default: merge this PR before opening app spec PRs.

### App spec PR

- Branch: `chore/INIT-{COMPONENT}-{NUMBER}-spec-<repo>`
- Target: `develop`
- Contains no product code.
- Engineering clarification happens on this PR.
- Product questions link back to a PRD amendment surface.
- Gate 2 requires the current Prayog workflow artifacts and applicable PE/dev
  reviews.
- Merge means the repo slice is ready to build.

### Wave PR

- Branch: `feature/INIT-{COMPONENT}-{NUMBER}-w{N}-{slug}`
- Target: `develop`
- One issue maps to one wave PR.
- Applicable live verification runs before grounding.
- Ground Report is committed before human approval.

## Board seed binding

Board seeding is an engineering-owned GitHub external action after spec PR
merge. The agent reads plan §9, checks existing issues, verifies `gh` auth, and
creates only missing wave issues after explicit authorization. If `gh` is
unavailable, it provides exact commands. `/pre-implement` remains blocked until
every expected wave issue exists.

## Q&A routing

| Lane | GitHub surface | Owner |
|------|----------------|-------|
| Product scope, UX, priority | PRD PR | PM |
| Engineering, ADR, interfaces, test policy | Spec PR | PE / senior engineer |
| Domain source of truth | PRD PR or linked issue | Domain SME |
| Auto-fixable naming/reference drift | Current artifact branch | Agent/developer |

## Launchpad responsibility

Launchpad:

- creates repositories/teams/project bindings,
- applies configured GitHub protection,
- scaffolds repositories,
- pins constitutions and Prayog,
- materializes runtime skill symlinks,
- provisions contract-declared labels and validates review-role bindings with
  `apply-gates`,
- writes the initial `AGENTS.md` when absent,
- verifies refs, contract, workflow, and runtime paths.

Launchpad does not redefine Prayog skill behavior or automatically cross human
and external-write gates.

## Related

- [Delivery model](delivery-model.md)
- [Branching policy](branching-policy.md)
- [Teams and RBAC](teams-and-rbac.md)
- [Harness pins](../harness/harness-pins.md)
- [Skills matrix](../harness/skills-matrix.md)
