# Tenant onboarding wizard

Q&A → **`onboarding.yaml`** → **`onboard plan`** (dry-run) → **`onboard apply`** (scaffold).

## Commands

| Command | Description |
|---------|-------------|
| `launchpad onboard interview` | Interactive Q&A → writes `onboarding.yaml` |
| `launchpad onboard plan --spec …` | Preview files and next steps (no writes) |
| `launchpad onboard show --spec …` | Print normalized spec |
| `launchpad onboard apply --spec …` | Scaffold meta, configs, templates, registry |

### Apply flags

| Flag | Purpose |
|------|---------|
| `--skip-registry` | Do not patch `clients.yaml` / `env.d` |
| `--skip-doctor` | Skip post-apply `launchpad doctor` |
| `--with-platform` | Run `setup-platform --apply` (GitHub + PAT) |

## Quick start (KOLA)

```bash
# Option A — interview
launchpad onboard interview
# writes ~/Workspace/handson/kola/onboarding.yaml (default paths from answers)

# Option B — copy example
cp examples/onboarding-kola.yaml ~/Workspace/handson/kola/onboarding.yaml

launchpad onboard plan --spec ~/Workspace/handson/kola/onboarding.yaml
launchpad onboard apply --spec ~/Workspace/handson/kola/onboarding.yaml
```

Do **not** set `options.seed_empty: false` unless repos already have history you must preserve.

After apply:

1. Paste token in `~/.config/launchpad/env.d/kola.env`
2. `launchpad --client kola setup-platform --config config/platform-kola-lab.yaml --apply`
3. PM: PR local meta content → `kola-meta/develop`

## GitLab

Set `forge.type: gitlab` in the spec (`examples/onboarding-kola-gitlab.yaml`). Apply generates GitLab-aware org config; automated `setup-platform` remains GitHub-first — see [multi-forge.md](multi-forge.md).

## Schema

[SCHEMA.md](SCHEMA.md#onboardingspec)

## Related

- [new-client.md](new-client.md)
- [setup-guide.md](setup-guide.md)
