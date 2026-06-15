# Diet Coke tenant example (hypothetical)

Fictional client used in [docs/setup-guide.md](../../docs/setup-guide.md).

| Item | Value |
|------|-------|
| Org | `kd_diet_coke` |
| Project slug | `diet_coke` |
| Meta repo | `diet_coke-meta` |
| App repos | `diet_coke-api`, `diet_coke-bff`, `diet_coke-registry` |

```bash
cp -r examples/diet_coke-meta ~/Workspace/handson/diet_coke/diet_coke-meta
cd ~/Workspace/handson/diet_coke/diet_coke-meta
# edit scripts/config/*.yaml — set your private rules repo in harness config
cp .env.example .env
export LAUNCHPAD_TENANT_ROOT="$(pwd)"
launchpad doctor
launchpad setup-platform --config scripts/config/platform-kd_diet_coke.yaml --dry-run
```

Do **not** commit `.env`. Push `diet_coke-meta` to your forge before running factory `--apply`.
