# Exit criteria — platform bootstrap

Use for **BOOTSTRAP-DS-001** closure (epic **E1**). After all items pass, run **INIT-PARICHAY-001** retro closure per [prd/INIT-PARICHAY-001.md](../prd/INIT-PARICHAY-001.md).

---

## Factory (<client>-meta)

- [ ] `launchpad verify-platform` — all checks green
- [ ] Example Engineering board live with custom fields
- [ ] `launchpad seed-work` applied for BOOTSTRAP-DS-001
- [ ] Wiki published: tenant <client>-meta/wiki
- [ ] Teams populated: `pm-team`, `backend-devs`, `release-managers`, …

---

## Parichay harness

- [ ] **P1** merged — AGENTS, skills, PR template, as-built columns (**v0.5.3**)
- [ ] **P2** merged — `example-api-testing-as-built.md` + `tests/README` feature map
- [ ] **R1** — `service-rules` **v0.5.4** tagged from harness audit
- [ ] **R2** — example-api submodule @ **v0.5.4**

---

## Process proof

- [ ] `/pre-implement` audition pass — [skills-audition.md](skills-audition.md)
- [ ] `/verify` audition pass (live smoke documented)
- [ ] Retro written: [retro/bootstrap-ds-001.md](retro/bootstrap-ds-001.md)

---

## Not required for bootstrap exit

- `tests/unit/` migration (delivered under INIT-PARICHAY-001 retro)
- example-bff, example-registry, Manthan on factory/board
- First product PRD / INIT manifest
