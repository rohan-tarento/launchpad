# Launchpad documentation

Process and factory docs for the launchpad kit. **Product content** (PRDs, planning) lives in each tenant `<slug>-meta` repo.

Pick the latest install tag from [CHANGELOG.md](../CHANGELOG.md) or [GitHub Releases](https://github.com/drivestream-lab/launchpad/releases).

---

## 1. Setup and usage

Join an **existing** programme on a new machine.

| Doc | Audience |
|-----|----------|
| [PM setup](setup/pm-setup.md) | Product — meta workspace, factory PAT |
| [Engineer setup](setup/engineer-setup.md) | Developer — app repo, no factory PAT |
| [Multi-laptop / client registry](setup/multi-laptop.md) | Install + `clients.yaml` (all roles) |

---

## 2. Onboarding a new tenant meta

Stand up a **new** programme from zero (platform operator).

| Doc | Content |
|-----|---------|
| [Tenant meta onboarding](onboarding/tenant-meta.md) | Config YAML, `init-client --meta`, harness, Day-N pointer |
| [Bootstrap prerequisites](onboarding/bootstrap-prerequisites.md) | PAT scopes, Team plan |
| [Factory CLI](onboarding/factory-cli.md) | `launchpad` commands reference |
| [Exit criteria](onboarding/exit-criteria.md) | Bootstrap exit checklist |

---

## 3. Scaffolding

| Doc | Content |
|-----|---------|
| [Scaffolding](scaffolding.md) | `apply-scaffold`, cookiecutter from `scaffold-<org>.yaml` |
| [Greenfield app repo](../playbook/operator/greenfield-app-repo.md) | Full Day-N sequence (init → scaffold → harness → forge) |

---

## 4. Contributing to launchpad

| Doc | Content |
|-----|---------|
| [Local development](contributing/local-dev.md) | Editable install, pytest, smoke |
| [Kit evolution](contributing/kit-evolution.md) | Tenant feedback → kit PR process |

---

## Reference

| Doc | Content |
|-----|---------|
| [SCHEMA.md](SCHEMA.md) | 5 YAML kinds |
| [stacks.md](stacks.md) | Stack registry |
| [CHANGELOG.md](../CHANGELOG.md) | Release notes and install tags |
| [Playbook](../playbook/README.md) | Delivery workflow, harness pins, RBAC |

---

## Architecture

```text
~/Workspace/example/
├── example-meta/              # control-plane (config, prd, work, wiki)
│   └── config/                # launchpad reads YAML from here
├── example-api/               # app repo (specs, code, harness pin)
└── …

~/.config/launchpad/           # per machine (never commit)
├── clients.yaml               # pointer to example-meta
└── env.d/example.env          # GITHUB_TOKEN (operators / PM only)
```

| Repo | Role |
|------|------|
| **launchpad** | Factory CLI + playbook kit |
| **`<slug>-meta`** | Programme config, PRDs, work manifests |
| **App repos** | Specs, code, harness pin, forge templates |
