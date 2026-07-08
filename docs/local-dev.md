# Local development (launchpad kit contributors)

For **operators** running factory commands against a tenant, use [multi-laptop.md](multi-laptop.md).

This guide is for **contributors** hacking on the launchpad repo itself.

---

## One-time editable install

```bash
cd ~/Workspace/drivestream-lab/launchpad
pipx install -e .
launchpad --version
```

Or use `./bin/launchpad` without pipx — it sets `PYTHONPATH` to the repo root.

---

## Run from source

```bash
export LAUNCHPAD_TENANT_ROOT=~/Workspace/drivestream-lab/launchpad/examples/tenant-meta

# Schema smoke
launchpad init-client --meta \
  --config-dir examples/tenant-meta/config \
  --dry-run

# Readiness check
launchpad status --meta \
  --config-dir examples/tenant-meta/config

# Doctor (no PAT required for config checks)
launchpad doctor
```

---

## Tests

```bash
# Install pytest once
pip install pytest

# Schema tests (fast, no network, no PAT)
pytest tests/test_schema.py -v

# Full test suite
pytest -v
```

---

## Smoke script

Runs dry-run commands against `examples/tenant-meta` — no PAT required:

```bash
./scripts/smoke-local.sh
```

---

## Test with a real tenant

```bash
cp -r examples/tenant-meta ~/Workspace/acme/acme-meta
# Edit config/*.yaml — replace example-org with your org name
# Rename *-example-org.yaml → *-<your-org>.yaml

launchpad --client acme doctor
launchpad init-client --meta \
  --config-dir ~/Workspace/acme/acme-meta/config \
  --dry-run
```

Register in `~/.config/launchpad/clients.yaml`:

```yaml
clients:
  - id: acme
    path: ~/Workspace/acme/acme-meta
    forge: github
```

---

## Project layout

| Path | Purpose |
|---|---|
| `launchpad/schema/` | 5-YAML schema validators (WS0) |
| `launchpad/forge/` | ForgeProvider protocol + GitHub implementation |
| `launchpad/commands/` | New 5-command implementations |
| `launchpad/onboarding/` | Interview flow (4 questions → 5 YAMLs) |
| `examples/tenant-meta/` | Smoke fixture — uses example-org |
| `tests/fixtures/schema/` | Day-1 / Day-N YAML fixtures |
| `tests/test_schema.py` | 36 schema unit tests |

---

## Forge (GitHub only)

v0.5.10 supports GitHub only.  GitLab is planned for v0.6.

```python
# Wrong — do not test forge type at runtime
if forge_type == "gitlab": ...

# Correct — use the ForgeProvider protocol
from launchpad.forge.providers import get_provider
provider_class = get_provider("github")  # raises NotImplementedError for "gitlab"
```
