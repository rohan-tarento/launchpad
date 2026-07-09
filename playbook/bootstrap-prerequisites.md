# Bootstrap prerequisites (v0.5.10)

Before `launchpad init-client --apply` succeeds end-to-end.

Full PAT setup: **[python-automation.md](python-automation.md)**.

---

## 1. Fine-grained PAT (factory)

Create a token scoped to your org per [python-automation.md](python-automation.md).

**Required organization permissions:**

| Permission | Access |
|------------|--------|
| Administration | Read and write |
| Issue types | **Read and write** |
| Members | Read and write |
| Projects | Read and write |

**Repository access:** All repositories (recommended). If selecting specific repos, include `<slug>-meta` and all app repos — a PAT that omits them returns 404 on repo API calls.

**Required repository permissions:**

| Permission | Access |
|------------|--------|
| Administration | Read and write |
| Contents | Read and write |
| Issues | Read and write |
| Pull requests | Read and write |
| Workflows | Read and write |

---

## 2. Branch protection requires GitHub Team plan

Branch protection rules require **GitHub Team** plan or higher. On free orgs:

| Option | Action |
|--------|--------|
| **A (recommended)** | Upgrade org to GitHub Team |
| **B (bootstrap only)** | Defer protection; use team push grants + manual merge discipline until upgrade |

---

## 3. Operator sequence

Configure client registry once — [multi-laptop.md](../docs/multi-laptop.md). Then:

```bash
launchpad doctor
launchpad whoami

# Day 1
launchpad init-client --meta --dry-run
launchpad init-client --meta --apply
launchpad apply-scaffold --meta --apply
launchpad apply-harness --meta --apply
launchpad status --meta

# Day N (repeat per repo)
launchpad init-client --repo <name> --apply
launchpad apply-scaffold --repo <name> --apply
launchpad apply-harness --repo <name> --apply
launchpad status --repo <name>

# Board seeding (after spec merge) — use gh per wave from plan §9
# See playbook/delivery-workflow.md
```
