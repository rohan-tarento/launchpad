# Multi-laptop setup

## Install launchpad once per machine

```bash
cd ~/Workspace/handson/launchpad
pipx install -e .
```

---

## Client registry (recommended)

One-time setup under `~/.config/launchpad/`:

```text
~/.config/launchpad/
├── clients.yaml          # tenant paths + default client
└── env.d/
    drivestream.env       # secrets (GITHUB_TOKEN) — one file per client
    acme.env
```

### 1. Create `clients.yaml`

Copy [examples/clients.yaml.example](../examples/clients.yaml.example):

```yaml
default: drivestream

clients:
  - id: drivestream
    path: ~/Workspace/handson/drivestream/drivestream-meta
    forge: github
```

### 2. Create secrets file

Copy [examples/env.d/client.env.example](../examples/env.d/client.env.example):

```bash
mkdir -p ~/.config/launchpad/env.d
cp examples/env.d/client.env.example ~/.config/launchpad/env.d/drivestream.env
# Edit drivestream.env — paste GITHUB_TOKEN (never commit this file)
chmod 600 ~/.config/launchpad/env.d/drivestream.env
```

**Secrets SSOT:** `~/.config/launchpad/env.d/<id>.env` — not `<client>-meta/.env`.

### 3. Run from anywhere

```bash
launchpad clients              # list configured clients
launchpad doctor               # uses default client from clients.yaml
launchpad --client drivestream seed-work --config work/INIT-*.yaml --dry-run
```

Or set a shell default:

```bash
export LAUNCHPAD_CLIENT=drivestream   # same as --client drivestream
launchpad doctor
```

---

## Resolution order

Launchpad picks the tenant in this order:

1. `LAUNCHPAD_TENANT_ROOT` (explicit override — wins over everything)
2. `--client` / `LAUNCHPAD_CLIENT` → lookup in `clients.yaml`
3. `default:` in `clients.yaml`
4. Sole client in `clients.yaml` (when only one entry)
5. Auto-discovery from cwd (`.launchpad-version`, `config/`, `prd/` + `work/`)

Secrets load from `env.d/<client-id>.env` when a client is active.

---

## Adding another client

```yaml
# ~/.config/launchpad/clients.yaml
default: drivestream

clients:
  - id: drivestream
    path: ~/Workspace/handson/drivestream/drivestream-meta
  - id: acme
    path: ~/Workspace/handson/acme/acme-meta
```

```bash
# ~/.config/launchpad/env.d/acme.env
GITHUB_TOKEN=github_pat_acme_...
```

```bash
launchpad --client acme doctor
```

No `source` required.

---

## Pin versions

Tenant `.launchpad-version` should match `pipx list | grep launchpad`.

---

## Legacy: manual env (still works)

```bash
export LAUNCHPAD_TENANT_ROOT=~/Workspace/handson/drivestream/drivestream-meta
export GITHUB_TOKEN=github_pat_...
launchpad doctor
```

Prefer the registry when you have multiple clients.
