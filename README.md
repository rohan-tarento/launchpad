# Launchpad  ·  v0.5.12

**YAML-driven forge factory and harness engineering kit for multi-tenant engineering programmes.**

Launchpad is not a "create GitHub repos" script.  It is a repeatable kit for running product delivery
where **specs are truth**, **agents have a pinned constitution**, and **factory automation enforces
the process** — gitflow, project board, constitution submodules, agent skills.

---

## Five commands.  No arguments to remember.

```
launchpad onboard interview          # Day 0  — 4 questions → 5 YAML files + registry
launchpad init-client --meta         # Day 1  — meta repo on GitHub (teams, gitflow, board)
launchpad apply-scaffold --meta      # Day 1  — scaffold from YAML (optional)
launchpad apply-harness  --meta      # Day 1  — pin constitution + seed skills
launchpad status  --meta      # Any    — verify harness is correct
```

All commands are **dry-run by default** — pass `--apply` to execute.
All commands require `--meta` or `--repo <name>` (no `--all` flag).
YAML is the single source of truth — no CLI arguments override config.

---

## Five YAML files

| File | Purpose |
|---|---|
| `config/programme.yaml` | Identity: name, org, workspace, forge provider |
| `config/governance-<org>.yaml` | GitHub: teams, repos, gitflow policy, project board |
| `config/harness-<org>.yaml` | Constitution (rules submodule) + agent skills per stack |
| `config/scaffold-<org>.yaml` | Cookiecutter template sources per repo |
| `config/service-catalog-<org>.yaml` | Service map (required; meta live + app examples) |

The interview writes all five on Day 0.  You edit them incrementally on Day N.

---

## Install

```bash
pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.5.12"
launchpad --version
```

---

## Greenfield walkthrough

### Day 0 — Local setup

```bash
launchpad onboard interview
```

4 questions.  Output:
```
  Programme name:   KOLA
  Programme slug:   kola
  GitHub org:       apex-common
  Workspace path:   ~/Workspace/kola
```

Writes:
```
~/Workspace/kola/kola-meta/config/
  programme.yaml
  governance-apex-common.yaml
  harness-apex-common.yaml
  scaffold-apex-common.yaml
  service-catalog-apex-common.yaml
~/.config/launchpad/clients.yaml     ← id: kola registered
~/.config/launchpad/env.d/kola.env  ← PAT stub
```

Prints:
```
NEXT:
  1. Open ~/.config/launchpad/env.d/kola.env and set GITHUB_TOKEN
  2. chmod 600 ~/.config/launchpad/env.d/kola.env
  3. launchpad --client kola doctor
```

### Day 1 — Meta repo on GitHub

```bash
source ~/.config/launchpad/env.d/kola.env
launchpad init-client --meta --dry-run    # preview
launchpad init-client --meta --apply      # execute
```

Creates team, repo, gitflow, project board.  Idempotent — safe to re-run.

### Day 1 — Scaffold and harness (optional)

```bash
# Edit config/scaffold-apex-common.yaml: set meta.enabled: true
launchpad apply-scaffold --meta --apply

launchpad apply-harness --meta --apply
launchpad status --meta
```

### Day N — Add an app repo

```bash
# Edit governance-apex-common.yaml: add the repo
launchpad init-client --repo kola-platform-core --apply

# Edit scaffold-apex-common.yaml: add the repo
launchpad apply-scaffold --repo kola-platform-core --apply

launchpad apply-harness --repo kola-platform-core --apply
launchpad status --repo kola-platform-core
```

### Any time — Readiness check

```bash
launchpad status --meta
launchpad status --repo kola-platform-core
```

---

## Stacks

Starter stacks built in (no configuration needed):

| Stack | Use |
|---|---|
| `meta-pm` | Programme management meta repo |
| `python-backend` | Python / FastAPI microservice |
| `nextjs-frontend` | Next.js frontend or BFF |
| `terraform-iac` | Terraform infrastructure-as-code |

Add custom stacks in `governance-<org>.yaml` — no kit-code changes required.  
See [docs/stacks.md](docs/stacks.md).

---

## Scaffold is fully YAML-driven

The kit does not own any template keys.  All `context:` fields are passed
free-form to cookiecutter.  Template owners evolve their `cookiecutter.json`
without any Launchpad changes.

```yaml
# scaffold-apex-common.yaml
repos:
  kola-platform-core:
    enabled: true
    template: gh:drivestream-lab/python-fastapi-foundation
    ref: v2.0.0
    context:
      project_name: kola-platform-core
      has_kafka: true          # template owner adds this param tomorrow
      has_postgres: true       # no Launchpad change needed
```

---

## Forge support

| Provider | Status |
|---|---|
| GitHub | Supported (v0.5.12) |
| GitLab | Planned (v0.6) |

---

## Docs

| Document | Purpose |
|---|---|
| [docs/greenfield.md](docs/greenfield.md) | Day-0 to Day-N walkthrough with KOLA example |
| [docs/SCHEMA.md](docs/SCHEMA.md) | 5 YAML kinds reference |
| [docs/stacks.md](docs/stacks.md) | Stack registry + adding custom stacks |
| [docs/kit-evolution.md](docs/kit-evolution.md) | Multi-tenant feedback and kit release process |
| [docs/multi-laptop.md](docs/multi-laptop.md) | Client registry across machines |
| [docs/local-dev.md](docs/local-dev.md) | Kit contributors — editable install + testing |
| [playbook/](playbook/) | SDD, delivery workflow, harness pins |

---

## Contributing

Standard `fork → branch → PR` to `drivestream-lab/launchpad`.  
See [docs/kit-evolution.md](docs/kit-evolution.md) for the tenant feedback → kit PR process.

---

## License

MIT — see [LICENSE](LICENSE).
