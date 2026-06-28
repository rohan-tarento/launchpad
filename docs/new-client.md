# New client onboarding

Checklist. Full walkthrough: **[setup-guide.md](setup-guide.md)**. Wizard (recommended): **[onboarding-wizard.md](onboarding-wizard.md)**.

## Checklist

1. **Install Launchpad** (once per machine) — [multi-laptop.md](multi-laptop.md) (`pipx install -e .`)
2. **Client registry** — `~/.config/launchpad/clients.yaml` + `env.d/<id>.env` for secrets
3. **Copy tenant skeleton** — `cp -r examples/tenant-meta ~/Workspace/handson/<client>/<client>-meta`
4. **Push meta** to your forge (meta is **not** created by `bootstrap-org`)
5. **Edit `config/*.yaml`** — org, repos, gitflow, harness; rename files to `*-<org>.yaml`
6. **`launchpad doctor`**
7. **`launchpad setup-platform --config config/platform-<org>.yaml --apply`**
8. **`launchpad verify-platform`**
9. Clone app repos as siblings → **`launchpad sync-harness --repo <app> --apply`**
10. PRD → `work/INIT-*.yaml` → **`launchpad seed-work --apply`**

## Workspace layout

```text
~/Workspace/handson/
├── launchpad/           # kit (separate repo)
└── <client>/
    ├── <client>-meta/   # from examples/tenant-meta/
    └── <app-repos>/     # siblings
```

## Per-machine config

One-time: [multi-laptop.md](multi-laptop.md)

```text
~/.config/launchpad/
├── clients.yaml
└── env.d/
    <client-id>.env      # GITHUB_TOKEN — chmod 600
```

```bash
launchpad --client <client-id> doctor
launchpad setup-platform --apply
```

## Legacy: manual env (CI only)

```bash
export LAUNCHPAD_TENANT_ROOT=$HOME/Workspace/handson/<client>/<client>-meta
export GITHUB_TOKEN=github_pat_...
```

Prefer the client registry for day-to-day use.

## Docs

| Guide | Content |
|-------|---------|
| [setup-guide.md](setup-guide.md) | End-to-end setup |
| [multi-laptop.md](multi-laptop.md) | Install + client registry |
| [local-dev.md](local-dev.md) | Kit contributors — venv / source |
| [playbook/bootstrap-prerequisites.md](../playbook/bootstrap-prerequisites.md) | PAT scopes |
