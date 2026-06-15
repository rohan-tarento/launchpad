# New client onboarding

Short checklist. Full walkthrough: **[setup-guide.md](setup-guide.md)** (hypothetical **diet_coke** project, org `kd_diet_coke`).

## Checklist

1. **Install Launchpad** (once) — clone or `pipx install`; see [local-dev.md](local-dev.md)
2. **Create `<client>-meta`** — copy [`examples/diet_coke-meta/`](../examples/diet_coke-meta/) or [`examples/tenant-meta/`](../examples/tenant-meta/)
3. **Push meta** to your forge (meta is **not** created by `bootstrap-org`)
4. **Edit `scripts/config/*-<org>.yaml`** — org, repos, gitflow, harness, project
5. **`.env`** — fine-grained `GITHUB_TOKEN` (never commit)
6. **`launchpad doctor`**
7. **`launchpad setup-platform --config scripts/config/platform-<org>.yaml --apply`**
8. **`launchpad verify-platform`**
9. Clone app repos as siblings → **`launchpad sync-harness --repo <app> --apply`**
10. First INIT: PRD → `work/INIT-*.yaml` → **`launchpad seed-work --apply`**

## Workspace layout

```text
~/Workspace/handson/
├── launchpad/              # kit (separate repo — do not copy into meta)
└── diet_coke/              # example client folder
    ├── diet_coke-meta/     # tenant
    └── diet_coke-api/      # app repos (siblings)
```

## Per-laptop env (optional)

```bash
mkdir -p ~/.config/launchpad/env.d
cat > ~/.config/launchpad/env.d/diet_coke.env <<'EOF'
export GITHUB_TOKEN=github_pat_...
export LAUNCHPAD_TENANT_ROOT=$HOME/Workspace/handson/diet_coke/diet_coke-meta
EOF
source ~/.config/launchpad/env.d/diet_coke.env
```

## Docs

| Guide | Content |
|-------|---------|
| [setup-guide.md](setup-guide.md) | End-to-end diet_coke example |
| [local-dev.md](local-dev.md) | Source / smoke testing |
| [multi-laptop.md](multi-laptop.md) | Multiple machines |
| [playbook/bootstrap-prerequisites.md](../playbook/bootstrap-prerequisites.md) | PAT scopes |
