# Launchpad Config Schema Reference (v0.5.10)

Every operator-facing configuration lives in YAML files inside your meta repo's
`config/` directory.  The CLI treats YAML as the **single source of truth** —
no runtime arguments, no hardcoded mappings.

---

## Five YAML kinds

| Kind | File | Required | Purpose |
|---|---|---|---|
| `Programme` | `config/programme.yaml` | Yes | Identity spine: name, org, forge |
| `GovernanceConfig` | `config/governance-<org>.yaml` | Yes | GitHub teams, repos, gitflow, board |
| `HarnessConfig` | `config/harness-<org>.yaml` | Yes | Constitution + skills per stack |
| `ScaffoldConfig` | `config/scaffold-<org>.yaml` | Yes | Cookiecutter sources per repo |
| `ServiceCatalog` | `config/service-catalog-<org>.yaml` | Yes | Service map (day-1 meta only) |

On Day 1 only the meta repo is live.  App repos are placed as YAML comments in
`governance.yaml`, `scaffold.yaml`, and `service-catalog.yaml` and promoted
incrementally.

---

## Programme

**File:** `config/programme.yaml`

```yaml
apiVersion: launchpad/v1
kind: Programme
programme: KOLA                # Human name of the initiative
programme_slug: kola           # Lowercase machine id; auto-derived if omitted
org: apex-common               # GitHub org slug (exact spelling)
meta_repo: kola-meta           # Control-plane repo name
workspace: ~/Workspace/kola    # Local parent dir for clones (supports ~)
forge:
  provider: github                # Only "github" is supported in v0.5.10
```

**Rules:**
- `programme_slug` must match `~/.config/launchpad/clients.yaml` `id` field.
- `forge.provider: gitlab` is **rejected** with a clear error (planned v0.6).

---

## GovernanceConfig

**File:** `config/governance-<org>.yaml`

```yaml
apiVersion: launchpad/v1
kind: GovernanceConfig
org: apex-common

stack_profiles:             # Optional — starter set is always merged in
  go-backend: Go microservice   # Extend with custom stacks without kit changes

teams:
  - name: platform-core
    description: Platform owners
    privacy: closed         # "closed" | "secret"

repos:
  kola-meta:
    stack: meta-pm          # Required. Must be a key in stack_profiles.
    teams: [platform-core]  # Required. At least one team from teams[].
    visibility: private     # "private" | "public" | "internal"
    description: Control-plane

policy:
  default_branch: main
  require_pr_reviews: 1

project_board:
  enabled: true
  name: KOLA Board
```

**Rules:**
- `repos.<name>.stack` must exist in `stack_profiles` (starter + custom).
- `repos.<name>.teams` must reference declared team names — prevents typos.

---

## Starter Stack Registry

These stacks are always available without any configuration.

| Stack | Default use |
|---|---|
| `meta-pm` | Programme management & ADR meta repo |
| `python-backend` | Python / FastAPI microservice |
| `nextjs-frontend` | Next.js frontend or BFF |
| `terraform-iac` | Terraform infrastructure-as-code |

To add a new stack: add an entry to `stack_profiles` in `governance-<org>.yaml`.
No kit-code changes required.  See [docs/stacks.md](stacks.md).

---

## HarnessConfig

**File:** `config/harness-<org>.yaml`

```yaml
apiVersion: launchpad/v1
kind: HarnessConfig
org: apex-common

profiles:
  python-backend:
    constitution:
      repo: python-services-rules   # Rules submodule repo slug
      org: drivestream-lab          # Optional; defaults to drivestream-lab
      ref: v2.1.0                   # Required. Pin to a tag.
    skills:
      - repo: python-agent-skills
        ref: v1.0.0

  meta-pm:
    constitution:
      repo: meta-governance-rules
      ref: v1.0.0

# Per-repo profile overrides.
# If omitted, a repo's harness_profile defaults to its stack from governance.yaml.
repos:
  special-repo: python-backend
```

**Resolution order:** `repos.<name>` → `repo.stack` from governance → no harness.

---

## ScaffoldConfig

**File:** `config/scaffold-<org>.yaml`

Scaffold is **optional** and entirely **YAML-driven**.  The kit passes `context`
fields free-form to cookiecutter — no allowlists, no kit-owned key validation.
Template owners evolve their `cookiecutter.json` without Launchpad changes.

```yaml
apiVersion: launchpad/v1
kind: ScaffoldConfig
org: apex-common

meta:
  enabled: true
  engine: cookiecutter
  template: gh:drivestream-lab/tenant-meta-foundation  # gh: | git+https:// | /local/path
  ref: v1.0.0
  context:                          # Free-form — passed directly to cookiecutter
    project_name: KOLA
    programme_slug: kola
    github_org: apex-common

repos:
  kola-platform-core:
    enabled: true
    engine: cookiecutter
    template: gh:drivestream-lab/python-fastapi-foundation
    ref: v2.0.0
    context:
      project_name: kola-platform-core
      has_kafka: true
      has_postgres: true
```

**Template shorthand:**
- `gh:<org>/<repo>` → `https://github.com/<org>/<repo>`
- `git+https://...` → arbitrary git URL
- `/absolute/path` → local template directory

**Rules:**
- `enabled: true` requires both `template` and `ref`.
- `enabled: false` (or omitted): all other fields are ignored and scaffold is skipped.

---

## ServiceCatalog

**File:** `config/service-catalog-<org>.yaml`

The catalog is **required**.  On Day 1 only the meta repo is a `live` entry.

```yaml
apiVersion: launchpad/v1
kind: ServiceCatalog
org: apex-common

services:
  kola-meta:
    stack: meta-pm
    description: Control-plane for KOLA
    status: live              # "live" | "planned" | "deprecated"
    teams: [platform-core]
    links:
      repo: https://github.com/apex-common/kola-meta

  # ─── Day-N examples (uncomment when the repo is live) ───────────────────
  #
  # kola-platform-core:
  #   stack: python-backend
  #   description: Core platform microservice
  #   status: planned
  #   teams: [platform-core]
```

---

## Forge providers

| Provider | Status |
|---|---|
| `github` | Supported in v0.5.10 |
| `gitlab` | Planned (v0.6) — rejected with a clear error if used |

All provider-specific logic lives in `launchpad/forge/providers/`.  Adding a
new provider requires only implementing the `ForgeProvider` protocol there.

---

## Naming contract

| Concept | Example | Notes |
|---|---|---|
| `programme` | `KOLA` | Human name — used in board titles, docs |
| `programme_slug` | `kola` | Machine id — must be `[a-z][a-z0-9-]+` |
| `org` | `apex-common` | GitHub org — exact spelling |
| `meta_repo` | `kola-meta` | Control-plane repo in the org |
| `stack` | `python-backend` | Key in `stack_profiles`; drives harness profile |
| repo slug | `kola-platform-core` | GitHub repo name in the org |
