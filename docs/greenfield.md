# Greenfield Operator Guide (v0.5.10)

This guide walks a new operator through standing up a programme from zero.
We use **STRATUM** (org: `Sandvik-Common`) as the running example.

---

## Operator Cheat Sheet

```
Day 0 — Local setup
  launchpad onboard interview

Day 1 — Meta repo on GitHub
  launchpad init-client --meta --dry-run    # preview
  launchpad init-client --meta --apply      # execute

Day 1 — Scaffold meta (optional)
  # Edit config/scaffold-Sandvik-Common.yaml: set meta.enabled: true
  launchpad apply-scaffold --meta --apply

Day 1 — Pin meta harness
  launchpad apply-harness --meta --apply
  launchpad check-harness --meta

Day N — Add an app repo
  # Edit governance-Sandvik-Common.yaml: add repo block
  launchpad init-client --repo stratum-platform-core --apply

Day N — Scaffold the app repo
  # Edit scaffold-Sandvik-Common.yaml: add repos.<name> block
  launchpad apply-scaffold --repo stratum-platform-core --apply

Day N — Pin app repo harness
  launchpad apply-harness --repo stratum-platform-core --apply
  launchpad check-harness --repo stratum-platform-core

Any time — Readiness check
  launchpad status --meta
  launchpad status --repo stratum-platform-core
```

---

## Day 0 — Local Setup

### Prerequisites

- GitHub PAT with scopes: `repo`, `admin:org`, `project`, `delete_repo`
- `launchpad` installed:
  ```
  pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.5.10"
  ```

### Run the interview

```
launchpad onboard interview
```

The interview asks 4 questions:

```
  Programme name  (e.g. STRATUM): STRATUM
  Auto-derived slug: stratum
  Programme slug  (confirm or override) [stratum]:
  GitHub org  (e.g. Sandvik-Common): Sandvik-Common
  Workspace path [~/Workspace]: ~/Workspace/stratum
```

It then creates:

```
~/Workspace/stratum/stratum-meta/
  config/
    programme.yaml
    governance-Sandvik-Common.yaml
    harness-Sandvik-Common.yaml
    scaffold-Sandvik-Common.yaml
    service-catalog-Sandvik-Common.yaml
~/.config/launchpad/clients.yaml     ← id: stratum registered
~/.config/launchpad/env.d/stratum.env  ← PAT stub
```

**NEXT printed by the command:**
```
1. Open ~/.config/launchpad/env.d/stratum.env
   Replace github_pat_REPLACE_ME with your GitHub PAT
2. chmod 600 ~/.config/launchpad/env.d/stratum.env
3. launchpad --client stratum doctor
```

---

## Day 1 — Meta Repo on GitHub

Source the secrets, then dry-run first:

```bash
source ~/.config/launchpad/env.d/stratum.env

launchpad init-client --meta --dry-run
```

Output shows what will happen:
```
init-client  →  Sandvik-Common/stratum-meta

  [dry-run] ensure team: Sandvik-Common/platform-core
  [dry-run] ensure repo: Sandvik-Common/stratum-meta (private)
  [dry-run] add team platform-core → Sandvik-Common/stratum-meta (push)
  [dry-run] ensure default branch: Sandvik-Common/stratum-meta@main
  [dry-run] ensure branch protection: Sandvik-Common/stratum-meta@main
  [dry-run] ensure project board: Sandvik-Common / "Sandvik-Common Board"
  [dry-run] link Sandvik-Common/stratum-meta → project dry-run-node-id
  [dry-run] ensure clients.yaml entry: id=stratum

NEXT: launchpad apply-scaffold --meta --apply
```

When satisfied, apply:

```bash
launchpad init-client --meta --apply
```

Then clone locally:

```bash
cd ~/Workspace/stratum
gh repo clone Sandvik-Common/stratum-meta
```

---

## Day 1 — Scaffold Meta (optional)

Edit `config/scaffold-Sandvik-Common.yaml` to enable the meta scaffold:

```yaml
meta:
  enabled: true
  engine: cookiecutter
  template: gh:drivestream-lab/tenant-meta-foundation
  ref: v1.0.0
  context:
    project_name: STRATUM
    programme_slug: stratum
    github_org: Sandvik-Common
```

Then scaffold:

```bash
launchpad apply-scaffold --meta --apply
```

---

## Day 1 — Pin Meta Harness

```bash
launchpad apply-harness --meta --apply
launchpad check-harness --meta
```

Output:
```
check-harness  →  Sandvik-Common/stratum-meta  [profile: meta-pm]
  ✔  constitution  meta-governance-rules@v1.0.0
  ✔  AGENTS.md

  check-harness: OK
```

---

## Day N — Add an App Repo

### Step 1: Edit governance YAML

In `config/governance-Sandvik-Common.yaml`, add:

```yaml
teams:
  - name: platform-core
    description: Platform owners
    privacy: closed
  # NEW:
  - name: hitl-dev
    description: HITL application developers
    privacy: closed

repos:
  stratum-meta:
    stack: meta-pm
    teams: [platform-core]
  # NEW:
  stratum-platform-core:
    stack: python-backend
    teams: [platform-core]
    visibility: private
    description: Core platform microservice
```

### Step 2: init-client

```bash
launchpad init-client --repo stratum-platform-core --dry-run
launchpad init-client --repo stratum-platform-core --apply
```

### Step 3: Edit scaffold YAML

In `config/scaffold-Sandvik-Common.yaml`, add:

```yaml
repos:
  stratum-platform-core:
    enabled: true
    engine: cookiecutter
    template: gh:drivestream-lab/python-fastapi-foundation
    ref: v2.0.0
    context:
      project_name: stratum-platform-core
      has_kafka: true
      has_postgres: true
```

### Step 4: Scaffold and harness

```bash
launchpad apply-scaffold --repo stratum-platform-core --apply
launchpad apply-harness --repo stratum-platform-core --apply
launchpad check-harness --repo stratum-platform-core
```

### Step 5: Promote in service catalog

In `config/service-catalog-Sandvik-Common.yaml`, move the commented entry to live:

```yaml
services:
  stratum-meta:
    stack: meta-pm
    status: live
    ...

  stratum-platform-core:    # was a comment, now live
    stack: python-backend
    description: Core platform microservice
    status: live
    teams: [platform-core]
```

---

## Readiness Check (any time)

```bash
launchpad status --meta
launchpad status --repo stratum-platform-core
```

Output:
```
status  →  Sandvik-Common/stratum-meta

  [✔] Governance declared  (in governance-Sandvik-Common.yaml)
  [✔] Local clone          (~/Workspace/stratum/stratum-meta)
  [✔] Scaffold (meta)      (enabled)
  [✔] Harness pinned       (profile: meta-pm)

NEXT: launchpad check-harness --meta
```

---

## Upgrading a Constitution (Rules)

Pin a new ref in `config/harness-Sandvik-Common.yaml`:

```yaml
profiles:
  python-backend:
    constitution:
      repo: python-services-rules
      ref: v2.2.0    # bumped from v2.1.0
```

Then re-run for each affected repo:

```bash
launchpad apply-harness --repo stratum-platform-core --apply
launchpad check-harness --repo stratum-platform-core
```

---

## Further Reading

- [SCHEMA.md](SCHEMA.md) — 5 YAML kinds reference
- [stacks.md](stacks.md) — Adding custom stacks
- [kit-evolution.md](kit-evolution.md) — How the kit evolves across tenants
