# Multi-laptop setup (v0.5.11)

## Install launchpad once per machine

**Tenant operators (recommended)** — install a **released tag**:

```bash
pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.5.11"
launchpad --version
```

Match the version in your tenant `<slug>-meta/.launchpad-version`.

**Upgrade:**

```bash
pipx install --force "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.5.11"
launchpad --client <slug> doctor
```

**Kit contributors** (launchpad repo development only):

```bash
cd ~/Workspace/drivestream-lab/launchpad
pipx install -e .
```

Multi-tenant feedback and release policy: [kit-evolution.md](kit-evolution.md).

---

## Client registry

One-time setup under `~/.config/launchpad/`:

```text
~/.config/launchpad/
├── clients.yaml          # programme registry
└── env.d/
    ├── stratum.env        # secrets (GITHUB_TOKEN) — one file per programme
    └── kola.env
```

Generated automatically by `launchpad onboard interview`.

### Manual setup

#### 1. Create `clients.yaml`

```yaml
# ~/.config/launchpad/clients.yaml
clients:
  - id: stratum
    path: ~/Workspace/stratum/stratum-meta
    forge: github
  # - id: kola
  #   path: ~/Workspace/kola/kola-meta
  #   forge: github
```

The `id` must match `programme_slug` in the programme's `config/programme.yaml`.

#### 2. Create secrets file

```bash
mkdir -p ~/.config/launchpad/env.d
cat > ~/.config/launchpad/env.d/stratum.env << 'EOF'
# stratum factory secrets — chmod 600
GITHUB_TOKEN=github_pat_REPLACE_ME
EOF
chmod 600 ~/.config/launchpad/env.d/stratum.env
```

**Secrets SSOT:** `~/.config/launchpad/env.d/<slug>.env` — never commit this file.

#### 3. Run from anywhere

```bash
source ~/.config/launchpad/env.d/stratum.env

launchpad clients              # list all registered programmes
launchpad doctor               # preflight check
launchpad --client stratum doctor
```

Or set a shell default:

```bash
export LAUNCHPAD_CLIENT=stratum
launchpad doctor
```

---

## Resolution order

Launchpad picks the tenant root in this order:

1. `LAUNCHPAD_TENANT_ROOT` (explicit override — wins over everything)
2. `--client` / `LAUNCHPAD_CLIENT` → lookup in `clients.yaml`
3. `default:` in `clients.yaml`
4. Sole client in `clients.yaml` (when only one entry)
5. Auto-discovery from cwd (`.launchpad-version` + `config/`)

Secrets load automatically from `env.d/<id>.env` when a client is active.

---

## Adding another programme

```yaml
# ~/.config/launchpad/clients.yaml
clients:
  - id: stratum
    path: ~/Workspace/stratum/stratum-meta
    forge: github
  - id: kola
    path: ~/Workspace/kola/kola-meta
    forge: github
```

```bash
# ~/.config/launchpad/env.d/kola.env  (chmod 600)
GITHUB_TOKEN=github_pat_kola_...
```

```bash
launchpad --client kola doctor
```

---

## Pin versions

Tenant `<slug>-meta/.launchpad-version` should match installed version:

```bash
cat ~/Workspace/stratum/stratum-meta/.launchpad-version   # should be 0.5.11
launchpad --version                                        # launchpad 0.5.11
```
