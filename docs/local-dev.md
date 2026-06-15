# Local development (source, no pip)

## One-time venv

```bash
cd ~/Workspace/handson/launchpad
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Run from source (any directory)

```bash
export LAUNCHPAD_TENANT_ROOT=~/Workspace/handson/launchpad/examples/tenant-meta
~/Workspace/handson/launchpad/launchpad doctor
~/Workspace/handson/launchpad/launchpad seed-work \
  --config work/INIT-EXAMPLE-001.yaml --dry-run
```

The `./launchpad` script sets `PYTHONPATH` to the repo root — no `pip install` required if deps are in `.venv`.

## Test tenant in another project

```bash
cp -r ~/Workspace/handson/launchpad/examples/tenant-meta ~/Workspace/handson/acme/acme-meta
export LAUNCHPAD_TENANT_ROOT=~/Workspace/handson/acme/acme-meta
~/Workspace/handson/launchpad/launchpad doctor
```

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

## Smoke script

```bash
./scripts/smoke-local.sh
```
