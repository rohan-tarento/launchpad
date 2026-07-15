# Spec: Rules Repository Rendering

## Objective

Fix `apply-harness` generation of target-repository `.harness-pin.yaml` files so
`rules.repo` contains exactly one organization prefix.

Engineers should be able to use either a bare constitution repository name or
an already-qualified `org/repo` value without generating
`drivestream-lab/drivestream-lab/python-services-rules`.

## Tech Stack

- Python 3.11+
- Existing `HarnessProfile` and `.harness-pin.yaml` template flow
- pytest
- No new dependencies

## Commands

```bash
# Focused command tests
python -m pytest tests/test_apply_harness_agents.py

# Full regression suite
python -m pytest
```

## Project Structure

- `launchpad/commands/apply_harness.py`: normalize and render
  `.harness-pin.yaml` `rules.repo`.
- `launchpad/templates/harness-pin.*.yaml`: existing source templates; no
  template format change required.
- `tests/test_apply_harness_agents.py`: focused rendering regression tests.

## Code Style

Use a small pure helper with explicit behavior:

```python
def _qualified_repo(org: str, repo: str) -> str:
    return repo if "/" in repo else f"{org}/{repo}"
```

Keep rendering logic deterministic and limited to the rules repository field.

## Functional Requirements

1. A bare constitution repo such as `python-services-rules` renders as
   `drivestream-lab/python-services-rules`.
2. An already-qualified constitution repo such as
   `drivestream-lab/python-services-rules` renders unchanged.
3. The generated value never duplicates the organization prefix.
4. The fix applies only to `.harness-pin.yaml` `rules.repo`.
5. Existing rule refs, skill entries, templates, config schema, and submodule
   pinning behavior remain unchanged.
6. Dry-run behavior remains unchanged because it does not write the pin file.

## Testing Strategy

- Add a regression test for an already-qualified constitution repo.
- Preserve or add coverage for a bare constitution repo.
- Assert parsed or exact generated `rules.repo` values.
- Run full pytest suite to catch harness-generation regressions.

No new coverage threshold is required.

## Boundaries

- Always: emit exactly one qualified `org/repo` value; test bare and qualified
  inputs.
- Ask first: add schema validation, change repository input contracts, or
  alter submodule URL construction.
- Never: modify `agent_skills.repo`, migrate harness config, or globally
  normalize all repository references as part of this fix.

## Success Criteria

- Qualified input produces
  `repo: drivestream-lab/python-services-rules`.
- Bare input produces the same qualified output.
- Output never contains
  `drivestream-lab/drivestream-lab/python-services-rules`.
- Existing apply-harness tests and full pytest suite pass.

## Open Questions

None.
