# Exit criteria — platform bootstrap

Use when closing the **first factory bootstrap** epic for a new tenant (repos, teams, gitflow, board, wiki).

---

## Factory (`<client>-meta`)

- [ ] `launchpad verify-platform` — all checks green
- [ ] Engineering project board live with custom fields
- [ ] Bootstrap work manifest seeded (if used)
- [ ] Wiki published from `wiki/` (optional)
- [ ] Teams populated: `pm-team`, `backend-devs`, `release-managers`, …

---

## Pilot app harness (`example-api` or first app repo)

- [ ] `launchpad sync-harness --apply` merged
- [ ] `launchpad verify-harness` passes
- [ ] Rules submodule + prayog-skills pin documented in harness config
- [ ] `/pre-implement` and `/verify` audition pass — [skills-audition.md](skills-audition.md)

---

## Not required for bootstrap exit

- Every app repo on the board
- First product PRD / product INIT
- Full CI gate on `main` (enable `options.require_ci` after workflow PRs land)

---

## Related

- [bootstrap-prerequisites.md](bootstrap-prerequisites.md)
- [setup-guide.md](../docs/setup-guide.md)
