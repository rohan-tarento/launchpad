# Stacks Reference

A **stack** is a named technology profile declared in YAML. It drives **harness**
(which rules + prayog profile apply). Scaffold is separate — opt-in per repo in
`scaffold-<org>.yaml`.

---

## YAML is SSOT

The kit does **not** ship a built-in stack registry. Everything is declared in
your meta repo:

| File | What you declare |
|------|------------------|
| `governance-<org>.yaml` → `stack_profiles` | Stack names your programme uses |
| `governance-<org>.yaml` → `repos.*.stack` | Which stack each repo uses |
| `harness-<org>.yaml` → `profiles` | Constitution + skills per stack |
| `scaffold-<org>.yaml` → `repos.*` | Cookiecutter source **only if** you scaffold |

**Brownfield:** omit or disable scaffold — run `apply-harness` only.

**Greenfield:** add a scaffold block with `enabled: true`, `template`, `ref`, and
`context`. No scaffold YAML entry → launchpad does not scaffold that repo.

---

## Adding a stack

1. Add to `stack_profiles` in `config/governance-<org>.yaml`:

```yaml
stack_profiles:
  meta-pm: Programme management & ADR meta repo
  python-backend: Python / FastAPI microservice
  go-backend: Go microservice
```

2. Add a matching profile to `config/harness-<org>.yaml`:

```yaml
profiles:
  go-backend:
    constitution:
      repo: go-services-rules
      ref: v1.0.0
    skills: []
```

3. **Optional** — scaffold block in `config/scaffold-<org>.yaml` (greenfield only):

```yaml
repos:
  my-go-service:
    enabled: true
    engine: cookiecutter
    template: gh:myorg/go-service-foundation
    ref: v1.0.0
    context:
      project_name: my-go-service
      has_grpc: true
```

4. Declare the repo in `config/governance-<org>.yaml`:

```yaml
repos:
  my-go-service:
    stack: go-backend    # must match a key in stack_profiles
    teams: [platform-core]
    visibility: private
```

No Launchpad kit code change required.

---

## Example stacks (documentation only)

These are common Drivestream patterns — **not** merged into your config automatically.
Copy into `stack_profiles` / `harness` / `scaffold` when you adopt them.

| Stack | Typical use | Typical constitution repo |
|---|---|---|
| `meta-pm` | Programme management & ADR meta repo | (none — meta repos) |
| `python-backend` | Python / FastAPI microservice | `python-services-rules` |
| `nextjs-frontend` | Next.js frontend or BFF | `nextjs-bff-rules` |
| `terraform-iac` | Terraform infrastructure-as-code | `terraform-infra-rules` |
| `data-platform` | Data platform / analytics | `data-platform-rules` |

---

## Stack → Harness Resolution

When you run `apply-harness --repo <name>`:
1. Launchpad reads `governance-<org>.yaml` to find the repo's `stack`
2. Checks `harness-<org>.yaml` for a `repos.<name>` override
3. Falls back to the stack name as the profile name
4. If no profile found → prints a hint to add the profile and exits cleanly

A repo can use a different harness profile than its stack (monorepos, special cases).

---

## Scaffold is independent of stack

Scaffold configuration in `scaffold-<org>.yaml` is fully independent.
`stack` drives harness only — not which cookiecutter template runs.

The same stack (e.g. `python-backend`) can use different foundation templates per
repo. If a repo has no scaffold block or `enabled: false`, `apply-scaffold` does
nothing for that repo.
