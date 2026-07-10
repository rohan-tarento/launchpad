# PM setup

Join an **existing** programme as PM on a new machine. Meta repo is already on GitHub.

For standing up a **new** programme, see [tenant meta onboarding](../onboarding/tenant-meta.md).

---

## Mental model

| Layer | Where | Your access |
|-------|-------|-------------|
| Config YAML | `example-meta/config/` | Write (PRs to meta) |
| PRDs / planning | `example-meta/prd/` | Write |
| Factory CLI | launchpad on your machine | Run `--meta` commands |
| Skill symlinks | `.harness/skills/`, `.agents/skills/*/` | Local only — rebuilt by `apply-harness` |

Launchpad reads harness and governance rules from **meta config**, then applies them to repos.

---

## Prerequisites

- [ ] launchpad installed — see [multi-laptop.md](multi-laptop.md) (`<tag>` from [CHANGELOG.md](../../CHANGELOG.md))
- [ ] Factory PAT in `~/.config/launchpad/env.d/example.env` — [bootstrap prerequisites](../onboarding/bootstrap-prerequisites.md)
- [ ] `gh auth login` for day-to-day git
- [ ] Write access to `example-org/example-meta`

---

## One-time machine setup

### 1. Install + registry

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

```bash
# ~/.config/launchpad/env.d/example.env  (chmod 600)
GITHUB_TOKEN=github_pat_REPLACE_ME
```

```bash
launchpad --client example doctor
```

### 2. Clone meta

```bash
gh repo clone example-org/example-meta ~/Workspace/example/example-meta
cd ~/Workspace/example/example-meta
git checkout develop
git submodule update --init --recursive
```

### 3. Materialize harness + forge

Symlinks are **not committed** — run after every fresh clone:

```bash
launchpad --client example apply-harness --meta --apply
launchpad --client example apply-forge-templates --meta --apply
launchpad --client example status --meta
```

Nothing to push for symlinks (gitignored). Commit only if pin file, `AGENTS.md`, or submodule refs changed.

### 4. Open workspace

Open **`example-meta`** in Cursor. Process: [delivery workflow](../../playbook/ship/delivery-workflow.md).

---

## Daily work

| Task | Where |
|------|-------|
| Author PRD | `example-meta/prd/` → meta PR |
| PM skills (`/validate-requirements`, etc.) | Cursor in meta after `apply-harness --meta` |
| Register new app repo | Edit `config/` → `init-client --repo` — see [greenfield app repo](../../playbook/operator/greenfield-app-repo.md) |
| Readiness check | `launchpad --client example status --meta` |

---

## What to commit vs not

| Commit | Do not commit |
|--------|---------------|
| PRDs, `config/` changes | `~/.config/launchpad/env.d/` |
| `.harness-pin.yaml`, `AGENTS.md` | `.harness/skills/` symlinks |
| Submodule gitlinks (prayog-skills, community) | `.agents/skills/<skill>/` symlinks (except prayog submodule) |

See [harness pins](../../playbook/harness/harness-pins.md) for the full boundary.

---

## Pin bump

When platform updates harness YAML in meta:

```bash
git pull origin develop
git submodule update --init --recursive
launchpad --client example apply-harness --meta --apply
launchpad --client example status --meta
```

Commit pin/submodule changes if needed. Re-run `apply-harness` locally even when you do not push symlinks.

---

## Checklist

```markdown
- [ ] launchpad installed @ tag matching example-meta/.launchpad-version
- [ ] clients.yaml → example-meta path
- [ ] env.d/example.env with factory PAT
- [ ] launchpad --client example doctor green
- [ ] example-meta cloned on develop
- [ ] git submodule update --init --recursive
- [ ] apply-harness --meta --apply
- [ ] apply-forge-templates --meta --apply
- [ ] status --meta green
- [ ] example-meta open in Cursor
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `no client active` | Set `clients.yaml` or pass `--client example` |
| `GITHUB_TOKEN not set` | Fill `env.d/example.env` |
| Skills missing in Cursor | `apply-harness --meta --apply` |
| `status` shows skill path ✗ | `apply-harness --meta --apply` |
| Version mismatch | Match [CHANGELOG](../../CHANGELOG.md) tag to `.launchpad-version` |

---

## Related

- [Engineer setup](engineer-setup.md) — app repo, no PAT
- [Multi-laptop](multi-laptop.md) — client registry
- [Delivery workflow](../../playbook/ship/delivery-workflow.md)
