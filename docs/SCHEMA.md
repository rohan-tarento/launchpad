# Launchpad YAML schema (`launchpad/v1`)

Legacy manifests may use `apiVersion: meta.meta/v1` during migration.

| kind | Purpose |
|------|---------|
| `OrgConfig` | Repos, labels, teams |
| `HarnessConfig` | Rules submodule + prayog-skills pins |
| `PlatformManifest` | Ordered `setup-platform` steps |
| `VerifyManifest` | Post-bootstrap checks |
| `WorkManifest` | `seed-work` — epic + wave issues |

Gitflow and project configs use the same `apiVersion` header without a separate `kind` in some files — see `examples/tenant-meta/scripts/config/`.

## Work manifest 1:1 rule (waves)

One wave ID → one board issue → one feature PR → one merge.

## Compatibility

`launchpad` loaders accept both `launchpad/v1` and `meta.meta/v1` `apiVersion` values.
