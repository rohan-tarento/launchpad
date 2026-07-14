# Changelog

All notable changes to the launchpad kit. Install a release tag:

```bash
pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@<tag>"
launchpad --version   # should match <slug>-meta/.launchpad-version
```

Pick `<tag>` from the latest section below or [GitHub Releases](https://github.com/drivestream-lab/launchpad/releases).

---

## [0.5.18rc3] — local RC

### Changed

- **`workspace` moved to `~/.config/launchpad/clients.yaml`** (machine-local).
  Shared `programme.yaml` must not contain `workspace` — schema fails closed.
- Clone layout: `clients[].workspace` or default `path.parent`.
- `onboard interview` writes `path` + `workspace` into clients.yaml only.

### Removed

- **`LAUNCHPAD_TENANT_ROOT`** — unused env override; docs and examples purged.
  Use `--client` / `clients.yaml`, or `--config-dir` for scripts.

## [0.5.18rc2] — local RC

### Added

- `board-bind` command — resolve programme engineering board from governance YAML
  (read-only meta); optional `--apply` links repo(s) to the org Project.
- `programme.board_binding` helper — `project_board.number` and `url` support.
- `status --repo` prints programme board name/URL from governance.
- Delivery contract profile token `app` — stack-agnostic Gate 2 labels for any
  non-meta-pm harness profile.

### Changed

- `AGENTS.md` template includes programme board section (`{{BOARD_NAME}}`,
  `{{BOARD_URL}}`) for app repos with delivery contract.
- Delivery playbook and engineer-setup document `/board-seed` + `board-bind`.

## [0.5.18rc1] — local RC

### Added

- Delivery-contract/workflow verification against the pinned Prayog checkout.
- Contract recording in generated harness pins and `status` output.
- Initial AGENTS bootstrap for pinned workflow navigation.
- `apply-gates` dry-run/apply command for contract-declared labels and
  tenant review-role access validation.

### Changed

- Delivery playbook documents Draft spec PR, Gate 2 labels, PE attestation,
  and merge/board-seed/pre-implement sequencing.
- `INIT-spec-PR.md` template updated for `/spec-draft` PR-readiness flow.
- Optional `board-seed-gate.yml` workflow template validates `spec-lgtm` on merge.
- `apply-harness --repo` seeds delivery workflows (`ci.yml`, `policy-branch-name.yml`,
  `board-seed-gate.yml`) when `delivery_contract` is set on the harness profile.
- Existing team-owned `AGENTS.md` files are preserved in full on re-apply.
- Delivery playbook is an integration/binding guide; pinned Prayog owns stage transitions.
- Full test suite runs in CI; Prayog fixtures cover the complete PM/dev bundles.
- Version comparison supports prerelease tags such as `v0.5.18-rc.1`.

---

## [0.5.17] — 2026-07-10

### Added

- **`apply-harness`** seeds `.gitignore` harness block (`gitignore.harness` template) so skill symlink mirrors are ignored
- **`examples/tenant-meta/.gitignore`** — skeleton for Path B onboarding

### Changed

- Upgrades legacy `.agents/skills/*/` patterns to `.agents/skills/*` on re-apply (symlinks vs directories)

---

## [0.5.16] — 2026-07-10

### Added

- **`docs/`** four-pillar layout — setup, onboarding, scaffolding, contributing
- **`playbook/`** subdirs — `ship/`, `harness/`, `github/`, `operator/`, `wiki/`
- **`docs/onboarding/`** — bootstrap prerequisites, factory CLI, exit criteria
- **`examples/agent-prompt-templates.md`** — moved from playbook
- **`CHANGELOG.md`** at repo root as version SSOT for docs (`@<tag>`)

### Changed

- Onboarding docs folded: org setup → `tenant-meta.md`; Cursor ↔ GitHub → `engineer-setup.md`
- **`apply-harness`** preserves existing `AGENTS.md` **Run and verify** section on re-sync
- Harness docs aligned with gitignored skill symlinks + tracked submodules model
- Kit templates and cross-links updated for new paths

### Removed

- Flat `playbook/*.md` files at playbook root (replaced by subdirs + `docs/onboarding/`)
- Obsolete `docs/` files (setup-guide, greenfield, onboarding-wizard, blog, etc.) — no redirects
- **`setup.py`** — unused wheel hook; packaging is `pyproject.toml` only (`launchpad/templates/` via `package-data`)

---

## [0.5.15] — 2026-07-10

### Added

- **`apply-forge-templates`** — seed `.github/ISSUE_TEMPLATE/` and `pull_request_template.md` from kit + governance
- Harness skill **hub** materialization with **community skills** support
- **`print_next_box`** — shared CLI helper for consistent NEXT output across commands
- Forge template staleness checks in **`status`**

### Changed

- **`status`** — forge template drift detection; hub + runtime skill path checks
- Kit issue templates use governance placeholders (`{{REPO_LIST_YAML}}`, `{{BOARD_URL}}`, etc.)

---

## [0.5.14] — 2026-07-09

### Added

- Harness skill **hub** (`.harness/skills/<name>/`) mirrored into `skill_runtimes` (default `.agents/skills`, `.claude/skills`)
- **`community_skills`** and **`skill_runtimes`** on harness profiles; community submodules under `.harness/community/`
- **`prayog_profile`** optional alias when harness stack name differs from prayog profile filename

### Changed

- **`apply-harness`** resolves skill names from prayog `profiles/*.yaml` at pinned ref (no Python fallbacks)
- **`status`** checks hub + all runtime paths; fails if prayog profile missing at pinned ref

---

## [0.5.13] — 2026-06

### Added

- **`CODEOWNERS.terraform-iac`** and **`harness-pin.terraform-iac.yaml`** harness templates
- Terraform-iac stack examples and docs

### Changed

- **`apply-harness`** substitutes `terraform-infra-rules` in harness pin templates
- **`init-client`** creates `develop` from `main` (`policy.integration_branch`) and protects both branches
- **`apply-harness`** pins constitution and prayog-skills as git submodules; improved tag fetch/checkout
- **`status --repo`** skills submodule drift check
- **`apply-scaffold`** helpful `--force` hint when output directory already exists
- Restore **`github_ops.py`** for GitHub forge (teams, repos, branch protection, projects)

---

## [0.5.11] — 2026-05

### Changed

- Align playbook, docs, examples, and templates with the 5-command CLI (remove stale commands)
- **`apply-harness`** seeds agent skills under **`.agents/skills/`** (removes legacy `.cursor/skills` submodule)
- Wiki publish documented as manual git flow (no `publish-wiki` CLI)

---

## [0.5.10] — 2026-04

### Added

- **5-YAML config model** — programme, governance, harness, scaffold, service-catalog
- **5-command CLI** — `onboard interview`, `init-client`, `apply-scaffold`, `apply-harness`, `status`
- **`onboard interview`** — 4 questions → writes config YAMLs + client registry + PAT stub
- GitHub-only forge (GitLab planned)

### Removed

- Legacy commands: `setup-gitflow`, `seed-work`, `bootstrap-project`, public `onboard apply/plan/show`

---

## Earlier releases

See git history and [GitHub Releases](https://github.com/drivestream-lab/launchpad/releases) for pre-0.5.10 tags.
