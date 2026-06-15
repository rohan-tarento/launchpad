# Multi-forge

Launchpad supports **two forges** with the same playbook and work manifests.

## GitHub (v1 — implemented)

- Org, teams, repos, branch protection
- Issues + Projects v2 custom fields
- `launchpad setup`, `seed-work`, `verify`

See [playbook/github-project.md](../playbook/github-project.md).

## GitLab (v1 — seed-work + labels)

- Group = `org` field in org config
- `forge.type: gitlab` in `scripts/config/org-<org>.yaml`
- Issues + scoped labels (`status::`, `codebase::`, `initiative::`)
- Example: `examples/tenant-meta/scripts/config/org-gitlab.example.yaml`

Full factory bootstrap on GitLab is incremental; `seed-work` is supported today.

## Redmine

**Out of scope** as a forge adapter. Redmine is PM-only; use GitLab issues for engineering SSOT. Link Redmine tickets from GitLab issue descriptions if a client requires both.

## Tenant config (future)

```yaml
forge:
  type: github   # or gitlab
  host: https://gitlab.com
  group: acme
```
