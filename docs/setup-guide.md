# Setup guide (v0.5.12)

End-to-end onboarding for a new programme.

Launchpad (the kit) and `<slug>-meta` (the tenant) are **separate repos**.
Install Launchpad once; the interview generates `<slug>-meta/config/` per programme.

For the full day-by-day walkthrough with a KOLA example, see **[greenfield.md](greenfield.md)**.

---

## Architecture

```text
~/Workspace/<slug>/
├── <slug>-meta/          # control-plane repo (config, prd, work, wiki)
│   └── config/
│       ├── programme.yaml
│       ├── governance-<org>.yaml
│       ├── harness-<org>.yaml
│       ├── scaffold-<org>.yaml
│       └── service-catalog-<org>.yaml
├── <app-api>/            # app repo clones (siblings of meta)
└── <app-bff>/
```

| Repo | Role |
|------|------|
| **launchpad** | Factory CLI + playbook — not copied into meta |
| **`<slug>-meta`** | Programme config, PRDs, work manifests, wiki |
| **App repos** | Specs, code, harness pin |

---

## Phase 0 — Prerequisites

1. GitHub org exists (org admin access).
2. Fine-grained PAT — scopes: `repo`, `admin:org`, `project`, `delete_repo`.
   See [playbook/bootstrap-prerequisites.md](../playbook/bootstrap-prerequisites.md).

`gh auth login` is for day-to-day PRs. Factory uses `GITHUB_TOKEN` in `env.d/`.

---

## Phase 1 — Install Launchpad (once per machine)

```bash
pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.5.12"
launchpad --version
```

See [multi-laptop.md](multi-laptop.md) for the client registry setup.

---

## Phase 2 — Interview (Day 0)

```bash
launchpad onboard interview
```

4 questions → writes 5 YAML files, patches `clients.yaml`, creates `env.d/<slug>.env` stub.

```
  Programme name:   KOLA
  Programme slug:   kola       (auto-derived, confirm)
  GitHub org:       apex-common
  Workspace path:   ~/Workspace/kola
```

Output:
```
~/Workspace/kola/kola-meta/config/
  programme.yaml
  governance-apex-common.yaml
  harness-apex-common.yaml
  scaffold-apex-common.yaml
  service-catalog-apex-common.yaml

~/.config/launchpad/clients.yaml  ← id: kola registered
~/.config/launchpad/env.d/kola.env  ← PAT stub (chmod 600, fill token)
```

**NEXT printed by the command** — follow it exactly.

---

## Phase 3 — Doctor

```bash
source ~/.config/launchpad/env.d/kola.env
launchpad --client kola doctor
```

Checks: token valid, programme.yaml found, version pin, GitHub API reachable.

---

## Phase 4 — Meta repo on GitHub (Day 1)

```bash
launchpad init-client --meta --dry-run    # preview
launchpad init-client --meta --apply      # execute
```

Creates: GitHub team(s), meta repo, gitflow (main branch + protection), project board.
All idempotent — re-run after fixing config.

Clone locally:

```bash
gh repo clone <org>/<slug>-meta ~/Workspace/<slug>/<slug>-meta
```

---

## Phase 5 — Scaffold meta (optional)

Edit `config/scaffold-<org>.yaml`: set `meta.enabled: true`, `template`, `ref`, `context`.

```bash
launchpad apply-scaffold --meta --apply
```

---

## Phase 6 — Pin meta harness

Edit `config/harness-<org>.yaml`: set `constitution.ref` to a pinned tag.

```bash
launchpad apply-harness --meta --apply
launchpad status --meta
```

---

## Phase 7 — App repos (Day N, incremental)

For each app repo:

1. Edit `config/governance-<org>.yaml` — add repo block (stack + teams required)
2. `launchpad init-client --repo <name> --apply`
3. Edit `config/scaffold-<org>.yaml` — add repo block
4. `launchpad apply-scaffold --repo <name> --apply`
5. `launchpad apply-harness --repo <name> --apply`
6. `launchpad status --repo <name>`
7. Edit `config/service-catalog-<org>.yaml` — promote from `planned` → `live`

---

## Phase 8 — First INIT

**PM (meta PRD PR):**
1. Author `prd/INIT-<id>.md` → meta PR
2. Run `/validate-requirements` → `/prd-impact-map`

**Dev (app spec PR):**
1. Open `chore/INIT-*-spec-<repo>` branch
2. Run `/spec-draft` → `/spec-implementation-plan` (§9 → wave issues)

See [playbook/delivery-workflow.md](../playbook/delivery-workflow.md).

---

## What Launchpad automates vs what stays manual

| Step | Launchpad | Manual |
|------|-----------|--------|
| Create GitHub org | | ✓ |
| Generate 5 config YAMLs | ✓ `onboard interview` | edit to customize |
| Create teams + meta repo | ✓ `init-client --meta` | add members in UI |
| Gitflow + board | ✓ `init-client` | |
| Scaffold app repo | ✓ `apply-scaffold` | |
| Pin harness | ✓ `apply-harness` | |
| Verify harness | ✓ `status` | |
| Create issues | — | `gh issue create` per wave from plan §9 |

---

## Docs

- [greenfield.md](greenfield.md) — Day-0 through Day-N walkthrough
- [new-client.md](new-client.md) — checklist
- [multi-laptop.md](multi-laptop.md) — install + client registry
- [SCHEMA.md](SCHEMA.md) — 5 YAML kinds reference
- [stacks.md](stacks.md) — stack registry + custom stacks
- [local-dev.md](local-dev.md) — kit contributors
