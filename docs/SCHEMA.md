# Launchpad YAML schema (`launchpad/v1`)

All factory YAML uses this header:

```yaml
apiVersion: launchpad/v1
kind: <KindName>
```

| kind | Purpose |
|------|---------|
| `OrgConfig` | Repos, labels, teams |
| `GitflowConfig` | Branch/merge/PR policy, teams, repo profiles |
| `HarnessConfig` | Rules submodule + prayog-skills pins |
| `PlatformManifest` | Ordered `setup-platform` steps |
| `VerifyManifest` | Post-bootstrap checks |
| `ProjectConfig` | GitHub Project board + fields |
| `WorkManifest` | `seed-work` — epic + wave issues |

Gitflow and project configs include `apiVersion` and `kind` — see [`examples/tenant-meta/scripts/config/`](../examples/tenant-meta/scripts/config/).

## Work manifest 1:1 rule (waves)

One wave ID → one board issue → one feature PR → one merge.
