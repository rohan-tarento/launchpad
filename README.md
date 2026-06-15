# Launchpad

Repeatable engineering kit for multi-client projects: **forge factory**, **generic playbook**, and **tenant scaffolding**.

Agent skills: **[prayog-skills](https://github.com/drivestream-lab/prayog-skills)** (install via harness pin).  
MDC / rules repos stay **private** and are **pinned** from each tenant meta repo.

## What this is

| Layer | Repo | Visibility |
|-------|------|------------|
| Kit | **launchpad** (this repo) | Public |
| Skills | prayog-skills | Public |
| Tenant | `<client>-meta` | Private — PRDs, planning, wiki, configs |
| Constitution | `your-org/*-rules` | Private — pinned via harness |

**Workspace root:** `/Users/kumar.deepak1/Workspace/handson/`

## Quick start (source — no pip)

```bash
cd ~/Workspace/handson/launchpad
python3 -m venv .venv && .venv/bin/pip install -e .

export LAUNCHPAD_TENANT_ROOT=~/Workspace/handson/launchpad/examples/tenant-meta
./bin/launchpad doctor
./bin/launchpad seed-work --config work/INIT-EXAMPLE-001.yaml --dry-run
```

See [docs/local-dev.md](docs/local-dev.md) for testing in another project.

## Tenant layout

Each `<client>-meta` private repo holds **product layers** (with real content):

- `prd/` — INIT PRDs and validation reports  
- `planning/` — pre-build archive  
- `programs/` — programme overviews  
- `work/` — manifests for `launchpad seed-work`  
- `wiki/` — client wiki pages  
- `scripts/config/` — org-specific factory YAML  

Empty structure: [`examples/tenant-meta/`](examples/tenant-meta/).

## CLI

```bash
launchpad doctor
launchpad whoami
launchpad setup --apply
launchpad seed-work --config work/INIT-*.yaml --apply
launchpad sync-harness --repo <app> --apply
launchpad verify-harness
```

Set `LAUNCHPAD_TENANT_ROOT` when not running from the tenant directory.

## Forges

| Forge | Status |
|-------|--------|
| GitHub | **v1** — full factory |
| GitLab | **v1** — `seed-work` + label-based fields |

## Docs

| Document | Purpose |
|----------|---------|
| [playbook/README.md](playbook/README.md) | Process SSOT |
| [docs/local-dev.md](docs/local-dev.md) | Source / bin/launchpad local testing |
| [docs/multi-laptop.md](docs/multi-laptop.md) | Multiple machines |
| [docs/PUBLICATION_CHECKLIST.md](docs/PUBLICATION_CHECKLIST.md) | Before publishing changes |
| [docs/SCHEMA.md](docs/SCHEMA.md) | `launchpad/v1` YAML kinds |

## Schema

Config and manifests use `apiVersion: launchpad/v1`. Legacy `meta.meta/v1` manifests are accepted during migration.

## License

MIT — see [LICENSE](LICENSE).
