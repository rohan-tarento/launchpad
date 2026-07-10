# Tenant meta — no local templates/

Launchpad kit `templates/` is the SSOT. Seed contributor artifacts with:

```bash
launchpad apply-forge-templates --meta --apply
launchpad apply-forge-templates --repo <name> --apply
```

Org-specific data (repo list, board URL) comes from `config/governance-<org>.yaml`, not duplicated files in meta.

See [launchpad templates/](https://github.com/drivestream-lab/launchpad/tree/main/templates).
