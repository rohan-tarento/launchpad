# Engineer setup

Join an **existing** app repo on a new machine. PM/platform has already onboarded the programme.

---

## Mental model

| Layer | Where | Your access |
|-------|-------|-------------|
| Code + specs | `example-api/` | Write (PRs to `develop`) |
| Config YAML | `example-meta/config/` | Read-only clone (launchpad reads this) |
| PRDs | `example-meta/prd/` on GitHub | Read |
| Skill symlinks | `.harness/skills/`, `.agents/skills/*` | Local only — `apply-harness` after clone |

**Home repo:** `example-api`. Launchpad is setup/verify only — not your daily workbench.

---

## Prerequisites

- [ ] launchpad installed — [multi-laptop.md](multi-laptop.md) (`<tag>` from [CHANGELOG.md](../../CHANGELOG.md))
- [ ] `clients.yaml` pointing at `example-meta` — **no factory PAT**
- [ ] `gh auth login` for clone/push
- [ ] Write access to `example-org/example-api`

---

## Workspace layout

```text
~/Workspace/example/
├── example-meta/     # read-only — launchpad reads config/
└── example-api/      # primary — open in Cursor
```

Launchpad resolves harness rules from `example-meta/config/harness-example-org.yaml` when you run `--repo example-api`.

---

## One-time machine setup

### 1. Install + registry (no PAT)

```bash
pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@<tag>"
```

```yaml
# ~/.config/launchpad/clients.yaml
clients:
  - id: example
    path: ~/Workspace/example/example-meta
    forge: github
```

No `env.d` file needed. Skip `doctor` / `whoami` / `init-client`.

### 2. Clone meta (read-only) + app repo

```bash
gh repo clone example-org/example-meta ~/Workspace/example/example-meta
gh repo clone example-org/example-api ~/Workspace/example/example-api

cd ~/Workspace/example/example-api
git checkout develop
git submodule update --init --recursive
```

### 3. Materialize skills (required)

Symlinks are **not in git** — without this step Cursor skills will not load:

```bash
launchpad --client example apply-harness --repo example-api --apply
launchpad --client example status --repo example-api
```

Run `apply-forge-templates --repo example-api --apply` only if `.github/ISSUE_TEMPLATE/` is missing on `develop`.

No push needed for symlinks.

### 4. Local dev

```bash
cp .env.example .env    # if present
make setup && make check && make test
```

Open **`example-api`** in Cursor. Read `AGENTS.md` for process links and skill names.

---

## PM vs engineer

| | PM | Engineer |
|---|-----|----------|
| Factory PAT | ✔ | ✗ |
| `clients.yaml` | ✔ | ✔ |
| Clone meta | ✔ write | ✔ read-only |
| Clone app | optional | ✔ primary |
| `apply-harness` | `--meta` | `--repo example-api` |
| `init-client` / `doctor` | ✔ | skip |
| Commits to meta | ✔ | ✗ |

---

## Daily work

| Task | Tool |
|------|------|
| Implement feature | Cursor + dev skills in app repo |
| Open PR | `gh` / GitHub |
| Read PRD | GitHub `example-meta/prd/` or local meta clone |
| Board | GitHub project / issue links |
| Process | `AGENTS.md` → [playbook](../../playbook/README.md) |

Do **not** run `apply-harness --meta` or commit to meta unless explicitly asked.

---

## Pin bump

When org updates harness pins:

```bash
cd ~/Workspace/example/example-meta && git pull    # refresh config read by launchpad
cd ~/Workspace/example/example-api
git pull && git submodule update --init --recursive
launchpad --client example apply-harness --repo example-api --apply
launchpad --client example status --repo example-api
```

Platform may open a `chore: sync harness pins` PR instead — review and merge.

---

## Checklist

```markdown
- [ ] launchpad installed @ tag matching example-meta/.launchpad-version
- [ ] clients.yaml → example-meta path (no env.d)
- [ ] example-meta cloned read-only
- [ ] example-api cloned on develop
- [ ] git submodule update --init --recursive (app repo)
- [ ] apply-harness --repo example-api --apply
- [ ] status --repo example-api green
- [ ] example-api open in Cursor
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `no client active` | `clients.yaml` + `--client example` |
| `config_dir not resolved` | Meta path in `clients.yaml` must exist on disk |
| Skills missing (`/spec-draft` etc.) | `apply-harness --repo example-api --apply` |
| `status` skill path ✗ | Same — re-run `apply-harness` |
| Forge templates missing | `apply-forge-templates --repo example-api --apply` |

---

## Cursor and GitHub

| Integration | Purpose |
|-------------|---------|
| **`gh auth login`** | Clone, push, PRs — day-to-day |
| **Cursor built-in Git** | Diff, commit, PR from IDE |
| **Factory PAT** | `launchpad` only — operators; you do not need one |

```bash
gh auth login
gh config set git_protocol https
gh auth status
gh repo list example-org
```

Open **`example-api`** (or parent workspace folder) in Cursor. Optional: Cursor Dashboard → Integrations → GitHub — grant **example-org** repos you use daily.

Factory automation uses **`GITHUB_TOKEN` in `~/.config/launchpad/env.d/`** on operator machines — separate from `gh auth`.

---

## Related

- [PM setup](pm-setup.md)
- [Multi-laptop](multi-laptop.md)
- [Harness pins](../../playbook/harness/harness-pins.md) — symlinks, submodules, pin file
- [SDD workflow](../../playbook/ship/sdd-workflow.md)
