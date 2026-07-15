# Implementation Plan: Rules Repository Rendering

## Overview

Fix `.harness-pin.yaml` rendering so `rules.repo` remains a single
organization-qualified repository path when the configured constitution repo
already contains its organization.

## Architecture Decisions

- Normalize only at `_seed_harness_pin` render boundary.
- Preserve a qualified repo string unchanged; prefix only bare repo strings.
- Keep template format, schema, submodule URLs, and skill rendering unchanged.
- Add direct unit coverage for the private pin-seeding function because it owns
  this output.

## Dependency Graph

```text
Repository qualification helper
        |
        +-- rules.repo template substitution
                |
                +-- bare and qualified rendering tests
                        |
                        +-- full regression suite
```

## Task List

### Phase 1: Render a canonical rules repository

- [ ] Task 1: Add a small qualification helper and use it only for
  `.harness-pin.yaml` `rules.repo`.
- [ ] Task 2: Add regression tests for bare and already-qualified constitution
  repo values.

### Checkpoint: Render fix

- [ ] Generated bare and qualified inputs both produce exactly
  `drivestream-lab/python-services-rules`.
- [ ] Generated output never contains a duplicate organization prefix.
- [ ] Focused tests pass.

### Phase 2: Regression verification

- [ ] Task 3: Run full pytest suite and review changed generated content.

### Checkpoint: Complete

- [ ] No code outside rendering and focused tests changed.
- [ ] All spec success criteria pass.
- [ ] Ready for review.

## Risks and Mitigations

- Template replacement is literal and supports several rules templates.
  Mitigation: retain existing replacement targets and change only replacement
  value.
- Bare repo values rely on configured `con.org`. Mitigation: test existing
  default-org behavior.

## Parallelization

Task 2 can be prepared alongside Task 1 but validates after Task 1. Task 3
depends on both.

## Open Questions

None.
