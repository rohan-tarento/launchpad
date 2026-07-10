# Multi-laptop setup (v0.5.13)

## Install launchpad once per machine

**Tenant operators (recommended)** — install a **released tag**:

```bash
pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.5.13"
launchpad --version
```

Match the version in your tenant `<slug>-meta/.launchpad-version`.

**Upgrade:**

```bash
pipx install --force "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.5.13"
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
    ├── kola.env           # secrets (GITHUB_TOKEN) — one file per programme
    └── example.env
```

Generated automatically by `launchpad onboard interview`.

### Manual setup

#### 1. Create `clients.yaml`

```yaml
# ~/.config/launchpad/clients.yaml
clients:
  - id: kola
    path: ~/Workspace/kola/kola-meta
    forge: github
  # - id: example
  #   path: ~/Workspace/example/example-meta
  #   forge: github
```

The `id` must match `programme_slug` in the programme's `config/programme.yaml`.

#### 2. Create secrets file

```bash
mkdir -p ~/.config/launchpad/env.d
cat > ~/.config/launchpad/env.d/kola.env << 'EOF'
# kola factory secrets — chmod 600
GITHUB_TOKEN=github_pat_REPLACE_ME
EOF
chmod 600 ~/.config/launchpad/env.d/kola.env
```

**Secrets SSOT:** `~/.config/launchpad/env.d/<slug>.env` — never commit this file.

#### 3. Run from anywhere

```bash
source ~/.config/launchpad/env.d/kola.env

launchpad clients              # list all registered programmes
launchpad doctor               # preflight check
launchpad --client kola doctor
```

Or set a shell default:

```bash
export LAUNCHPAD_CLIENT=kola
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
  - id: kola
    path: ~/Workspace/kola/kola-meta
    forge: github
  - id: example
    path: ~/Workspace/example/example-meta
    forge: github
```

```bash
# ~/.config/launchpad/env.d/example.env  (chmod 600)
GITHUB_TOKEN=github_pat_example_...
```

```bash
launchpad --client example doctor
```

---

## Pin versions

Tenant `<slug>-meta/.launchpad-version` should match installed version:

```bash
cat ~/Workspace/kola/kola-meta/.launchpad-version   # should be 0.5.13
launchpad --version                                        # launchpad 0.5.13
```
