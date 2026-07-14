# Local development

For **operators** running factory commands against a tenant, see [setup/multi-laptop.md](../setup/multi-laptop.md).

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
# Use --config-dir against the example tenant (no clients.yaml required for smoke)
launchpad init-client --meta \
  --config-dir examples/tenant-meta/config \
  --dry-run

# Readiness check
launchpad status --meta \
  --config-dir examples/tenant-meta/config

# Doctor (no PAT required for config checks)
launchpad doctor
```

For a full client registry entry when testing against a real clone:

```yaml
# ~/.config/launchpad/clients.yaml
clients:
  - id: example
    path: ~/Workspace/drivestream-lab/launchpad/examples/tenant-meta
    workspace: ~/Workspace/drivestream-lab/launchpad/examples
    forge: github
```

---

## Tests

```bash
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
|------|---------|
| `launchpad/schema/` | 5-YAML schema validators |
| `launchpad/forge/` | ForgeProvider protocol + GitHub implementation |
| `launchpad/commands/` | CLI command implementations |
| `launchpad/onboarding/` | `onboard interview` flow |
| `examples/tenant-meta/` | Smoke fixture — uses example-org |
| `tests/` | Unit tests |

---

## Forge

GitHub is supported today. GitLab is planned.

```python
from launchpad.forge.providers import get_provider
provider_class = get_provider("github")  # raises NotImplementedError for "gitlab"
```

---

## Related

- [Kit evolution](kit-evolution.md) — PR and release process
- [CHANGELOG.md](../../CHANGELOG.md) — release notes
