# Tenant onboarding wizard

Q&A → **`onboarding.yaml`** → **`onboard plan`** (dry-run) → **`onboard apply`** (scaffold).

## Status

| Command | Status |
|---------|--------|
| `onboard plan --spec …` | **Implemented** — preview files and next steps |
| `onboard show --spec …` | **Implemented** — print normalized spec |
| `onboard interview` | PR2 — interactive Q&A |
| `onboard apply --spec …` | PR3 — scaffold meta + registry |

## Quick start (KOLA)

```bash
cp examples/onboarding-kola.yaml ~/Workspace/handson/kola/onboarding.yaml
# edit org, repos, rules refs

launchpad onboard plan --spec ~/Workspace/handson/kola/onboarding.yaml
launchpad onboard show --spec ~/Workspace/handson/kola/onboarding.yaml
```

## GitLab

Set `forge.type: gitlab` in the spec (see `examples/onboarding-kola-gitlab.yaml`). Plan accepts the spec and prints a warning; full GitLab scaffold/platform apply remains incremental — see [multi-forge.md](multi-forge.md).

## Schema

[SCHEMA.md](SCHEMA.md#onboardingspec) · examples: [`onboarding-kola.yaml`](../examples/onboarding-kola.yaml)

## Related

- [new-client.md](new-client.md) — manual checklist (pre-wizard)
- [setup-guide.md](setup-guide.md) — post-scaffold factory bootstrap
