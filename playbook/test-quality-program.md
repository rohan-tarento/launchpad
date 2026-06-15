# Parichay test quality program

**Initiative:** `INIT-PARICHAY-001` (retro closure)  
**PRD:** [`prd/INIT-PARICHAY-001.md`](../prd/INIT-PARICHAY-001.md)

**Status:** Implementation **complete** on example-api `develop` (harness + waves W1–W5). This doc is operational reference only — not a new delivery epic.

**Prerequisite:** Harness pins @ v0.5.5 / v0.1.0; `launchpad verify-harness --repo example-api` passes.

---

## Goals

| Goal | Outcome |
|------|---------|
| **Structure** | `tests/unit/` + `testpaths = ["tests/unit"]` |
| **Unit coverage** | Business logic, branches, edges in `tests/unit/` |
| **Verify alignment** | Keep every `verify_<feature>.py`; trim to one live happy path per feature |
| **No overlap** | Same behavior not fully asserted in unit and verify |
| **Traceability** | `tests/README.md` feature map + as-built columns |

---

## Phase 4a — structure (done)

- `tests/unit/` created; `test_health.py` moved
- `pyproject.toml`, `Makefile`, `tests/README.md` updated
- Issue #27 / PR #35 merged

---

## Phase 4b — waves (done)

| Wave | Verify scripts | Unit focus | Issue |
|------|----------------|------------|-------|
| **W1** | `verify_oem_*_authentication` | Auth services, validation, error mapping | #28 |
| **W2** | `verify_oem_onboarding`, list users/creds | Onboarding service (mocked repos) | #29 |
| **W3** | `verify_device_token`, `verify_device_owner_authentication` | JWT/JTI/OTP (mock Redis) | #30 |
| **W4** | `verify_bridge_*`, `verify_mqtt_*`, `verify_device_traffic_catalog` | Catalog/ACL synthesis | #31 |
| **W5** | `verify_telemetry`, `verify_health` | Thin unit; stack proof in verify | #32 / PR #41 |

### Per-wave PR checklist (future test work)

- [ ] Spec / capability row touched (if behavior changes)
- [ ] `tests/unit/test_<area>.py` added or extended
- [ ] Matching verify script — representative happy path only
- [ ] `tests/README.md` feature map row updated
- [ ] As-built: `implementation-status.md` verification rows; `## Testing harness` if layout changes (Option B — no separate `testing-and-verification.md`)

---

## Board usage

**Example Engineering** board. Set **Initiative** = `INIT-PARICHAY-001`, **Codebase** = `example-api`. Move to **Verify** with live verify command in PR description.

---

## Related

- [INIT-PARICHAY-001 PRD](../prd/INIT-PARICHAY-001.md)
- [harness-pins.md](harness-pins.md)
- [pm-dev-handoff.md](pm-dev-handoff.md)
