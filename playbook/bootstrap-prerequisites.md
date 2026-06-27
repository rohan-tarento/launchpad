# Bootstrap prerequisites (example-org)

Before `launchpad setup-platform --apply` and `seed-work` succeed end-to-end.

---

## 1. Fine-grained PAT (factory)

Create a token scoped to **example-org** per [`python-automation.md`](python-automation.md).

**Required organization permissions:**

| Permission | Access |
|------------|--------|
| Administration | Read and write |
| Issue types | **Read and write** |
| Members | Read and write |
| Projects | Read and write |

**Repository access (critical):**

| Setting | Value |
|---------|--------|
| Resource owner | **example-org** |
| Repository access | **All repositories** (recommended) |

If you pick "Only select repositories", you **must** include at least **<client>-meta** and **example-api**. A PAT that omits them returns **404** on repo API calls — dry-run then looks like repos are missing and fails on labels.

**Required repository permissions** (on selected or all repos):

| Permission | Access |
|------------|--------|
| Administration | Read and write |
| Contents | Read and write |
| Issues | Read and write |
| Metadata | Read |

Store in **`~/.config/launchpad/env.d/<client-id>.env`** as `GITHUB_TOKEN=...` (chmod 600; never commit). See [multi-laptop.md](../docs/multi-laptop.md).

`gh auth token` is **not sufficient** for issue types API — board bootstrap will fail without Issue types on a fine-grained PAT.

---

## 2. Branch protection (private repos)

Classic **branch protection** on private repos requires **GitHub Team** or **GitHub Pro** on the owning account/org.

If `setup-gitflow` fails with:

```text
Upgrade to GitHub Pro or make this repository public to enable this feature.
```

**Options:**

| Option | Action |
|--------|--------|
| **A (recommended)** | Upgrade example-org org to GitHub Team |
| **B (bootstrap only)** | Defer protection; use team push grants + manual merge discipline until upgrade |
| **C** | Configure rulesets manually in GitHub UI after plan upgrade |

Partial gitflow still applies: `develop` branch, team push grants.

---

## 3. Operator sequence (after PAT in env.d)

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

---

## 4. Already done (initial push)

- Repo: tenant <client>-meta (`develop` + `main`)
- Labels on meta + example-api (bootstrap-org)
- Engineering teams created (release-managers, pm-team, backend-devs, …)
- `develop` branch on example-api (from main)

**Pending:** branch protection, project board, seed-work (need PAT + possibly GitHub Team).
