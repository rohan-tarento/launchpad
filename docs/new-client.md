# New client onboarding

Checklist. Full walkthrough: **[setup-guide.md](setup-guide.md)**.

## Checklist

1. **Install Launchpad** (once) — [local-dev.md](local-dev.md)
2. **Copy tenant skeleton** — `cp -r examples/tenant-meta ~/Workspace/handson/<client>/<client>-meta`
3. **Push meta** to your forge (meta is **not** created by `bootstrap-org`)
4. **Edit `scripts/config/*.yaml`** — org, repos, gitflow, harness; rename files to `*-<org>.yaml`
5. **`.env`** — `GITHUB_TOKEN` (never commit)
6. **`launchpad doctor`**
7. **`launchpad setup-platform --config scripts/config/platform-<org>.yaml --apply`**
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

## Per-laptop client registry (recommended)

One-time: [multi-laptop.md](multi-laptop.md) — `~/.config/launchpad/clients.yaml` + `env.d/<id>.env` for secrets.

```bash
launchpad --client drivestream doctor
launchpad setup-platform --apply
```

## Legacy: manual env (single client)

```bash
export LAUNCHPAD_TENANT_ROOT=$HOME/Workspace/handson/<client>/<client>-meta
export GITHUB_TOKEN=github_pat_...
```

## Docs

| Guide | Content |
|-------|---------|
| [setup-guide.md](setup-guide.md) | End-to-end setup |
| [local-dev.md](local-dev.md) | Smoke / source testing |
| [playbook/bootstrap-prerequisites.md](../playbook/bootstrap-prerequisites.md) | PAT scopes |
