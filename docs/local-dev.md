# Local development (launchpad kit contributors)

For **operators** running factory commands against a tenant, use [multi-laptop.md](multi-laptop.md) (`pipx install -e .` + client registry).

This guide is for **contributors** hacking on the launchpad repo itself.

---

## One-time venv

```bash
cd ~/Workspace/handson/launchpad
python3 -m venv .venv
.venv/bin/pip install -e .
```

Or use `./bin/launchpad` without activating the venv (uses `.venv` if present).

---

## Run from source

```bash
export LAUNCHPAD_TENANT_ROOT=~/Workspace/handson/launchpad/examples/tenant-meta
./bin/launchpad doctor
./bin/launchpad seed-work --config work/INIT-EXAMPLE-001.yaml --dry-run
```

The `./bin/launchpad` script sets `PYTHONPATH` to the repo root.

---

## Test tenant in another project

```bash
cp -r ~/Workspace/handson/launchpad/examples/tenant-meta ~/Workspace/handson/acme/acme-meta
```

Add to `~/.config/launchpad/clients.yaml`:

```yaml
clients:
  - id: acme
    path: ~/Workspace/handson/acme/acme-meta
```

Create `~/.config/launchpad/env.d/acme.env` with `GITHUB_TOKEN=...`, then:

```bash
launchpad --client acme doctor
```

---

## GitHub vs GitLab

Set `forge.type` in `scripts/config/org-<org>.yaml`:

```yaml
forge:
  type: github   # default
```

```yaml
forge:
  type: gitlab
  host: https://gitlab.com
```

`seed-work` dispatches automatically. GitLab uses scoped labels (`status::backlog`, `codebase::example-api`).

See `examples/tenant-meta/scripts/config/org-gitlab-example.yaml`.

---

## Smoke script

```bash
./scripts/smoke-local.sh
```

Uses `examples/tenant-meta` via `LAUNCHPAD_TENANT_ROOT` — no PAT required for dry-run.
