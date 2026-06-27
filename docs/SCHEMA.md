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
| `WikiConfig` | `publish-wiki` — wiki source dir, org, repo |
| `OnboardingSpec` | `onboard plan` / `onboard apply` — tenant bootstrap intent |

Gitflow and project configs include `apiVersion` and `kind` — see [`examples/tenant-meta/config/`](../examples/tenant-meta/config/).

## OnboardingSpec

Authoritative input for `launchpad onboard plan` and `launchpad onboard apply`. Lives beside the tenant workspace (e.g. `~/Workspace/handson/kola/onboarding.yaml`), not inside meta until you optionally commit it after apply.

Example: [`examples/onboarding-kola.yaml`](../examples/onboarding-kola.yaml) · GitLab stub: [`examples/onboarding-kola-gitlab.yaml`](../examples/onboarding-kola-gitlab.yaml)

| Field | Purpose |
|-------|---------|
| `client_id` | Registry id (`~/.config/launchpad/clients.yaml`) |
| `forge.type` | `github` \| `gitlab` |
| `org` / `meta_repo` | Forge org + meta repo name |
| `paths.workspace` | Parent dir; meta = `workspace/meta_repo` |
| `repos` | App repos for bootstrap (meta excluded) |
| `rules` | Private `*-rules` repos + initial tags |
| `gitflow` | Branch naming / CI switches for generated gitflow YAML |
| `registry` | Patch local client registry on apply |
| `provision` | Post-scaffold hooks (`run_setup_platform`, `run_doctor`) |

## Work manifest 1:1 rule (waves)

One wave ID → one board issue → one feature PR → one merge.
