# Tasks: Rules Repository Rendering

## Task 1: Normalize rendered rules repository

**Description:** Add a small pure helper that preserves an `org/repo` value and
prefixes a bare repository with the constitution organization. Use it only when
replacing `.harness-pin.yaml` `rules.repo`.

**Acceptance criteria:**
- [ ] Bare `python-services-rules` renders as
  `drivestream-lab/python-services-rules`.
- [ ] Qualified `drivestream-lab/python-services-rules` renders unchanged.
- [ ] `agent_skills.repo` and submodule behavior remain unchanged.

**Verification:**
- [ ] Inspect generated pin contents through focused tests.

**Dependencies:** None.

**Files likely touched:**
- `launchpad/commands/apply_harness.py`

**Estimated scope:** XS.

## Task 2: Test duplicate-organization regression

**Description:** Test direct pin generation for both bare and qualified rules
repository inputs.

**Acceptance criteria:**
- [ ] Qualified input does not generate
  `drivestream-lab/drivestream-lab/python-services-rules`.
- [ ] Bare input still generates a qualified repository.
- [ ] Rules ref remains rendered.

**Verification:**
- [ ] `python -m pytest tests/test_apply_harness_pin.py`

**Dependencies:** Task 1.

**Files likely touched:**
- `tests/test_apply_harness_pin.py`

**Estimated scope:** S.

## Task 3: Verify harness regression safety

**Description:** Run focused and full test suites after the render fix.

**Acceptance criteria:**
- [ ] Pin rendering test passes.
- [ ] Full test suite passes.

**Verification:**
- [ ] `python -m pytest tests/test_apply_harness_pin.py`
- [ ] `python -m pytest`

**Dependencies:** Tasks 1–2.

**Files likely touched:**
- No production files.

**Estimated scope:** XS.

## Checkpoint: Before implementation

- [ ] Tasks have explicit acceptance criteria and verification.
- [ ] Tasks are dependency ordered.
- [ ] Human approves this plan.
