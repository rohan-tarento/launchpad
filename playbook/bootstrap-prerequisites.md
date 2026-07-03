# Bootstrap prerequisites

Before `launchpad setup-platform --apply` and `seed-work` succeed end-to-end.

Full PAT setup + operator sequence: **[python-automation.md](python-automation.md)**.

---

## 1. Fine-grained PAT (factory)

Create a token scoped to your org per [`python-automation.md`](python-automation.md).

**Required organization permissions:**

| Permission | Access |
|------------|--------|
| Administration | Read and write |
| Issue types | **Read and write** |
| Members | Read and write |
| Projects | Read and write |

**Repository access:** All repositories (recommended). If selecting specific repos, include at least `<client>-meta` and all app repos — a PAT that omits them returns 404 on repo API calls.

**Required repository permissions:**

| Permission | Access |
|------------|--------|
| Actions | Read and write |
| Administration | Read and write |
| Contents | Read and write |
| Issues | Read and write |
| Pull requests | Read and write |
| Workflows | Read and write |

---

## 2. Branch protection requires GitHub Team plan

Branch protection rulesets (gitflow enforcement) require **GitHub Team** plan or higher. On free orgs:

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
launchpad setup-platform --dry-run
launchpad setup-platform --apply
launchpad verify-platform
launchpad seed-work --config work/INIT-<id>.yaml --dry-run
launchpad seed-work --config work/INIT-<id>.yaml --apply
```
