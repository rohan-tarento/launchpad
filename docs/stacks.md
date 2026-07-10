# Stacks Reference (v0.5.10)

A **stack** is a named technology profile that drives two things:
1. Which harness profile (constitution + skills) to apply to a repo
2. Which cookiecutter template to scaffold from (optional)

---

## Starter Stack Registry

These four stacks are built into Launchpad and always available.
No YAML configuration required to use them.

| Stack | Default use | Typical constitution repo |
|---|---|---|
| `meta-pm` | Programme management & ADR meta repo | `meta-governance-rules` |
| `python-backend` | Python / FastAPI microservice | `python-services-rules` |
| `nextjs-frontend` | Next.js frontend or BFF | `nextjs-frontend-rules` |
| `terraform-iac` | Terraform infrastructure-as-code | `terraform-infra-rules` |

---

## Adding a Custom Stack

You do not need to change any Launchpad kit code to add a new stack.
Add it to `stack_profiles` in `config/governance-<org>.yaml`:

```yaml
stack_profiles:
  go-backend: Go microservice
  java-spring: Java Spring Boot service
  data-pipeline: Python data/ML pipeline
```

Then:
1. Add a matching profile to `config/harness-<org>.yaml`:

```yaml
profiles:
  go-backend:
    constitution:
      repo: go-services-rules
      ref: v1.0.0
    skills: []
```

2. Add a scaffold block to `config/scaffold-<org>.yaml` if you want to scaffold new repos:

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

3. Declare the repo in `config/governance-<org>.yaml`:

```yaml
repos:
  my-go-service:
    stack: go-backend    # must match a key in stack_profiles
    teams: [platform-core]
    visibility: private
```

That's it — no Launchpad code change required.

---

## Stack → Harness Resolution

When you run `apply-harness --repo <name>`:
1. Launchpad reads `governance-<org>.yaml` to find the repo's `stack`
2. Checks `harness-<org>.yaml` for a `repos.<name>` override
3. Falls back to the stack name as the profile name
4. If no profile found → prints a hint to add the profile and exits cleanly

This means a repo can have a different harness profile than its stack
(useful for monorepos or special repos that share a stack but need
different rules).

---

## Scaffold is Independent of Stack

Scaffold configuration in `scaffold-<org>.yaml` is fully independent.
The `stack` on a repo only drives the harness — not the scaffold template.
This lets the same stack (e.g. `python-backend`) use different templates
for different repos (e.g. async-heavy vs sync-heavy foundations).
