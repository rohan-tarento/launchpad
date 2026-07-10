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
| Org name, repo list, team slugs | No | `config/governance-<org>.yaml` |
| Board title, project # | No | `config/governance-<org>.yaml` |
| Stack profiles, issue types | No | `config/governance-<org>.yaml` |
| PRDs, work manifests, wiki copy | No | `prd/`, `work/`, `wiki/` |
| Playbook **deltas** (enterprise quirks for one programme) | No | `<client>-meta/playbook/` |
| PAT, `clients.yaml` paths | No | `~/.config/launchpad/` (never commit) |

**Examples in this repo** use fictional programmes only (`kola`, `apex-common`, `example-org`) — see `examples/programme-kola.yaml` and `examples/tenant-meta/config/`.

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

Re-run idempotent factory commands only when release notes say so (`init-client`, `apply-harness`, etc.).

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
- [ ] No customer names in diff (see [PUBLICATION_CHECKLIST.md](PUBLICATION_CHECKLIST.md))
- [ ] Tag pushed: `v0.x.y`
- [ ] Tenant operators notified: version + any re-run commands

---

## Current release line (v0.5.13)

**v0.5.13** — terraform-iac harness templates:

- Add **`CODEOWNERS.terraform-iac`** and **`harness-pin.terraform-iac.yaml`** (cloud-agnostic; pairs with `terraform-azure-foundation` / future `terraform-aws-foundation`)
- **`apply-harness`** substitutes `terraform-infra-rules` in harness pin templates
- Examples and docs updated for `terraform-infra-rules` + Azure foundation scaffold context

**v0.5.14** — harness skill hub + YAML SSOT:

- **`apply-harness`** resolves skill names from prayog `profiles/*.yaml` at pinned ref (no Python fallbacks)
- Materializes `.harness/skills/<name>/` hub and mirrors into `skill_runtimes` (default `.agents/skills`, `.claude/skills`)
- **`community_skills`** and **`skill_runtimes`** on harness profiles; community submodules under `.harness/community/`
- **`prayog_profile`** optional alias when harness stack name differs from prayog profile filename
- **`status`** checks hub + all runtime paths; fails if prayog profile missing at pinned ref

**v0.5.13** — (installed kit baseline)


- **`init-client`** creates `develop` from `main` (`policy.integration_branch`) and protects both branches
- **`apply-harness`** pins constitution and prayog-skills as git submodules (unified governance model); progress messages; reliable tag fetch/checkout
- **`status --repo`** skills submodule drift check; PM view shows governance pins for rules + skills
- **`apply-scaffold`** helpful `--force` hint when output directory already exists (post init-client)
- Restore **`github_ops.py`** for GitHub forge (teams, repos, branch protection, projects)
- Governance examples: `integration_branch: develop`

**v0.5.11** — doc drift fix + harness skills path:

- Align playbook, docs, examples, and templates with the v0.5.10 5-command CLI (remove stale `setup-gitflow`, `seed-work`, `bootstrap-project`, etc.)
- **`apply-harness`** seeds agent skills under **`.agents/skills/`** (removes legacy `.cursor/skills` submodule)
- Wiki publish documented as manual git flow (no `publish-wiki` CLI)

**v0.5.10** introduced the greenfield refactor (5-YAML model, 5-command CLI, GitHub-only).

Tenants adopt by pinning `0.5.13` in `.launchpad-version` and installing from that tag.
