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
| `HarnessConfig` | Rules submodule + prayog-skills pins; optional per-repo `scaffold` cookiecutter overrides |
| `PlatformManifest` | Ordered `setup-platform` steps |
| `VerifyManifest` | Post-bootstrap checks |
| `ProjectConfig` | GitHub Project board + fields |
| `WorkManifest` | `seed-work` — epic + wave issues |
| `WikiConfig` | `publish-wiki` — wiki source dir, org, repo |
| `ServiceCatalog` | Repo → team, branch_code, owns/depends_on (PM skills, strict branches) |
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

## Scaffold profiles (`launchpad scaffold`)

Generates app repos from cookiecutter templates. Profiles are registered in launchpad (`python-backend` today; `frontend` / `nextjs-bff` planned).

| Profile | Template (default) | Harness `repos.<name>.profile` |
|---------|-------------------|--------------------------------|
| `python-backend` | `gh:autrio10x/python-fastapi-foundation` or local sibling | `python-backend` |
| `frontend` | planned `nextjs-bff-foundation` | `frontend` |

Optional per-repo overrides in `HarnessConfig`:

```yaml
repos:
  example-api:
    profile: python-backend
    service_name: Example API
    scaffold:
      has_postgres: "yes"
      has_redis: "yes"      # profile default; omit if default OK
      has_kafka: "yes"
      parichay_client: "yes"
      has_internal_api: "yes"
```

All keys: `auth_mode`, `has_postgres`, `has_redis`, `has_kafka`, `has_s3`, `has_cratedb`, `has_emqx`, `has_telemetry`, `has_internal_api`, `parichay_client`, `abhilekh_client`, `kavach_client`, `default_port`. See [greenfield-app-repo.md](../playbook/greenfield-app-repo.md).

## ServiceCatalog

Lives at `config/service-catalog-{org}.yaml` in tenant meta (same convention as `gitflow-{org}.yaml`, `harness-{org}.yaml`). Maintained by Launchpad — do not hand-author the full file from scratch.

| Command | When |
|---------|------|
| `onboard apply` | Initial catalog from OnboardingSpec repos |
| `sync-catalog --apply` | Merge from gitflow after adding repos (preserves curated fields) |
| `setup-platform --apply` | Final platform step writes/updates catalog |

| Field (per service) | Purpose |
|---------------------|---------|
| `name` | Repo name (key for merge) |
| `repo` | `{org}/{name}` |
| `team` | Engineering team slug from gitflow profile |
| `branch_code` | `{COMPONENT}` in `feature/INIT-{COMPONENT}-{NUMBER}-{slug}` |
| `description` | Human summary for PM/dev skills |
| `owns` | Capabilities this service provides (curate manually) |
| `depends_on` | Other service names (curate manually) |

Optional OnboardingSpec repo fields: `branch_code`, `owns`, `depends_on` — seeded on first generate only; later edits in meta are preserved by `sync-catalog`.
