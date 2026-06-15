# GitHub org setup — example-org

One-time and ongoing configuration for the **example-org** organization.

---

## Prerequisites

- [ ] Org admin access on **example-org**
- [ ] **GitHub Team** plan (branch protection on private repos)
- [ ] Factory PAT — [python-automation.md](python-automation.md)
- [ ] Optional: [GitHub CLI](https://cli.github.com/) — `gh auth login`

---

## 1. Organization settings

**GitHub → example-org → Settings → General**

| Setting | Recommendation |
|---------|----------------|
| Default repository permission | **Read** |
| Two-factor authentication | Required for members |

---

## 2. Factory bootstrap (v0 slice)

Repos in factory config: **<client>-meta**, **example-api**.

```bash
cd <client>-meta
cp .env.example .env
launchpad setup-platform --apply
launchpad verify-platform
launchpad seed-work --config work/INIT-<id>.yaml --apply
```

Config SSOT: `scripts/config/*-example-org.yaml`

---

## 3. Teams

Created by `setup-platform`. Add members:

https://github.com/orgs/example-org/teams

| Team | Role |
|------|------|
| `pm-team` | Meta `develop` merges; spec handoff branches on app repos |
| `backend-devs` | Parichay `develop` merges |
| `release-managers` | `main` only |
| `platform-devs` | Factory / meta automation |
| `frontend-devs` | BFF repos (when added) |
| `data-platform-devs` | Data platform repos (when added) |

Details: [teams-and-rbac.md](teams-and-rbac.md)

---

## 4. Project board

**Example Engineering** — [Project #1](https://github.com/orgs/example-org/projects/1)

Fields and columns: [github-project.md](github-project.md)

---

## 5. Wiki

Required for bootstrap: [wiki-setup.md](wiki-setup.md)

---

## Related

- [bootstrap-prerequisites.md](bootstrap-prerequisites.md)
- [github-enforcement.md](github-enforcement.md)
- [exit-criteria.md](exit-criteria.md)
