# Kit evolution — multi-tenant feedback into launchpad

How improvements discovered on **any** tenant deployment flow back into the **single** global kit (`drivestream-lab/launchpad`) without customer names, secrets, or tenant config in this repo.

Tenant-specific values live in **`<client>-meta`** (private per programme). This repo stays **generic**.

---

## Principles

1. **One kit, many tenants** — operators install a **tagged release** of launchpad; tenants pin `.launchpad-version` in meta.
2. **No customer names in the kit** — no enterprise customer org/repo/team names in committed docs, examples, tests, or changelog.
3. **Reusable fixes upstream** — if a second tenant could use it, it belongs here.
4. **Config stays in meta** — org names, team slugs, board titles, issue types, `set_default_branch: false`, etc.

---

## What belongs where

| Change type | Global launchpad | Tenant `<client>-meta` |
|-------------|------------------|------------------------|
| CLI bug / idempotent factory step | Yes | No |
| New gitflow or project option (generic) | Yes | No |
| Enterprise PAT limitation (documented generically) | Yes | No |
| Org name, repo list, team slugs | No | `config/org-*.yaml`, `gitflow-*.yaml` |
| Board title, project #, field options | No | `config/project-*.yaml` |
| Issue type names (Epic vs Feature) | No | `config/project-*.yaml` |
| PRDs, work manifests, wiki copy | No | `prd/`, `work/`, `wiki/` |
| Playbook **deltas** (enterprise quirks for one programme) | No | `<client>-meta/playbook/` |
| PAT, `clients.yaml` paths | No | `~/.config/launchpad/` (never commit) |

**Examples in this repo** use fictional programmes only (`kola`, `apex-common`, `example-org`) — see `examples/onboarding-kola.yaml`.

---

## Issue intake (any tenant)

### 1. Report

| Channel | Use for |
|---------|---------|
| **GitHub issue** on `drivestream-lab/launchpad` | Kit bugs, feature requests, docs gaps |
| **Tenant meta issue** (private) | Wrong YAML, PRD, wiki, customer-only process |
| **Internal ticket** (customer programme) | Triage before opening a kit issue |

**Issue template (kit):**

- **Symptom** — command + error (redact org/repo names; use `example-org` / `example-api`)
- **Expected** — generic behaviour
- **Classification** — `kit-bug` \| `kit-feature` \| `tenant-config` \| `tenant-content`
- **Found on** — internal reference only (e.g. “enterprise deployment #3”) — **not** customer name in public title

### 2. Triage (maintainers)

| Label | Action |
|-------|--------|
| `tenant-config` | Close with pointer: fix in `<client>-meta` |
| `kit-bug` / `kit-feature` | Schedule; reproduce with fictional org |
| `docs` | Playbook or `docs/` only — still no customer names |

### 3. Implement

- Branch from `main` on `drivestream-lab/launchpad`
- Reproduce with `examples/` or unit tests — **not** a customer clone
- PR description may mention “validated on an enterprise deployment” in prose — **diff must stay generic**
- Add/update tests where behaviour is new

### 4. Release

1. Merge PR to `main`
2. Tag semver: `git tag v0.x.y && git push origin v0.x.y`
3. Note in release summary (generic): features/fixes — no customer names
4. Notify tenant operators: bump `.launchpad-version` and reinstall

### 5. Tenant adoption

```bash
pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.x.y"
launchpad --version    # must match <client>-meta/.launchpad-version
launchpad --client <client> doctor
```

Re-run idempotent factory commands only when release notes say so (`setup-gitflow`, `bootstrap-project`, etc.).

---

## Learning propagation across tenants

```text
Tenant A finds gap → kit PR (generic) → tag v0.x.y
                                      ↓
Tenant B, C, … upgrade pip package → same fix, no merge from A's meta repo
```

Tenants do **not** fork launchpad. They do **not** share each other's meta repos. They share **releases**.

---

## Distribution policy (operators)

| Do | Don't |
|----|--------|
| `pipx install` from **git tag** on `drivestream-lab/launchpad` | `pipx install -e .` on a laptop fork for production use |
| Pin `.launchpad-version` in meta | Everyone on random `main` SHA |
| `launchpad doctor` after upgrade | Commit PAT or `clients.yaml` to git |

See [multi-laptop.md](multi-laptop.md) for install and client registry.

**Kit contributors** may use `pipx install -e .` locally; **tenant operators** install **released tags**.

---

## Release checklist (maintainers)

- [ ] CI / tests pass on `main`
- [ ] `pyproject.toml` + `launchpad/__init__.py` version bumped
- [ ] No customer names in diff (`rg -i 'sandvik\|stratum'`)
- [ ] Tag pushed: `v0.x.y`
- [ ] Tenant operators notified: version + any re-run commands

---

## Current release line (enterprise-ready features)

Target **v0.5.7** (pending merge) includes generic support for:

- Shared org / programme slug (`project_slug`, `repo_prefix`, prefixed team slugs)
- `options.set_default_branch: false` (enterprise org-owner workaround)
- `project.team_access` (Projects v2 team collaborators)
- `project.issue_types` in onboarding spec
- `sync-catalog` team names from gitflow `teams` map
- verify skips `gitflow.default_branch` when `set_default_branch: false`

Tenants adopt by pinning `0.5.7` in `.launchpad-version` and installing from that tag.
