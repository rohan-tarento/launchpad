# Greenfield Operator Guide (v0.5.13)

This guide walks a new operator through standing up a programme from zero.
We use **KOLA** (org: `apex-common`) as the running example.

---

## Operator Cheat Sheet

```
Day 0 — Local setup
  launchpad onboard interview

Day 1 — Meta repo on GitHub
  launchpad init-client --meta --dry-run    # preview
  launchpad init-client --meta --apply      # execute

Day 1 — Scaffold meta (optional)
  # Edit config/scaffold-apex-common.yaml: set meta.enabled: true
  launchpad apply-scaffold --meta --apply

Day 1 — Pin meta harness
  launchpad apply-harness --meta --apply
  launchpad status --meta

Day N — Add an app repo
  # Edit governance-apex-common.yaml: add repo block
  launchpad init-client --repo kola-platform-core --apply

Day N — Scaffold the app repo
  # Edit scaffold-apex-common.yaml: add repos.<name> block
  launchpad apply-scaffold --repo kola-platform-core --apply

Day N — Pin app repo harness
  launchpad apply-harness --repo kola-platform-core --apply
  launchpad status --repo kola-platform-core

Any time — Readiness check
  launchpad status --meta
  launchpad status --repo kola-platform-core
```

---

## Day 0 — Local Setup

### Prerequisites

- GitHub PAT with scopes: `repo`, `admin:org`, `project`, `delete_repo`
- `launchpad` installed:
  ```
  pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.5.13"
  ```

### Run the interview

```
launchpad onboard interview
```

The interview asks 4 questions:

```
  Programme name  (e.g. KOLA): KOLA
  Auto-derived slug: kola
  Programme slug  (confirm or override) [kola]:
  GitHub org  (e.g. apex-common): apex-common
  Workspace path [~/Workspace]: ~/Workspace/kola
```

It then creates:

```
~/Workspace/kola/kola-meta/
  config/
    programme.yaml
    governance-apex-common.yaml
    harness-apex-common.yaml
    scaffold-apex-common.yaml
    service-catalog-apex-common.yaml
~/.config/launchpad/clients.yaml     ← id: kola registered
~/.config/launchpad/env.d/kola.env  ← PAT stub
```

**NEXT printed by the command:**
```
1. Open ~/.config/launchpad/env.d/kola.env
   Replace github_pat_REPLACE_ME with your GitHub PAT
2. chmod 600 ~/.config/launchpad/env.d/kola.env
3. launchpad --client kola doctor
```

---

## Day 1 — Meta Repo on GitHub

Source the secrets, then dry-run first:

```bash
source ~/.config/launchpad/env.d/kola.env

launchpad init-client --meta --dry-run
```

Output shows what will happen:
```
init-client  →  apex-common/kola-meta

  [dry-run] ensure team: apex-common/platform-core
  [dry-run] ensure repo: apex-common/kola-meta (private)
  [dry-run] add team platform-core → apex-common/kola-meta (push)
  [dry-run] ensure default branch: apex-common/kola-meta@main
  [dry-run] ensure branch protection: apex-common/kola-meta@main
  [dry-run] ensure project board: apex-common / "apex-common Board"
  [dry-run] link apex-common/kola-meta → project dry-run-node-id
  [dry-run] ensure clients.yaml entry: id=kola

NEXT: launchpad apply-scaffold --meta --apply
```

When satisfied, apply:

```bash
launchpad init-client --meta --apply
```

Then clone locally:

```bash
cd ~/Workspace/kola
gh repo clone apex-common/kola-meta
```

---

## Day 1 — Scaffold Meta (optional)

Edit `config/scaffold-apex-common.yaml` to enable the meta scaffold:

```yaml
meta:
  enabled: true
  engine: cookiecutter
  template: gh:drivestream-lab/tenant-meta-foundation
  ref: v1.0.0
  context:
    project_name: KOLA
    programme_slug: kola
    github_org: apex-common
```

Then scaffold:

```bash
launchpad apply-scaffold --meta --apply
```

---

## Day 1 — Pin Meta Harness

```bash
launchpad apply-harness --meta --apply
launchpad status --meta
```

Output:
```
status  →  apex-common/kola-meta  [profile: meta-pm]
  ✔  constitution  meta-governance-rules@v1.0.0
  ✔  AGENTS.md

  status: OK
```

---

## Day N — Add an App Repo

### Step 1: Edit governance YAML

In `config/governance-apex-common.yaml`, add:

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
  kola-meta:
    stack: meta-pm
    teams: [platform-core]
  # NEW:
  kola-platform-core:
    stack: python-backend
    teams: [platform-core]
    visibility: private
    description: Core platform microservice
```

### Step 2: init-client

```bash
launchpad init-client --repo kola-platform-core --dry-run
launchpad init-client --repo kola-platform-core --apply
```

### Step 3: Edit scaffold YAML

In `config/scaffold-apex-common.yaml`, add:

```yaml
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

### Step 4: Scaffold and harness

```bash
launchpad apply-scaffold --repo kola-platform-core --apply
launchpad apply-harness --repo kola-platform-core --apply
launchpad status --repo kola-platform-core
```

### Step 5: Promote in service catalog

In `config/service-catalog-apex-common.yaml`, move the commented entry to live:

```yaml
services:
  kola-meta:
    stack: meta-pm
    status: live
    ...

  kola-platform-core:    # was a comment, now live
    stack: python-backend
    description: Core platform microservice
    status: live
    teams: [platform-core]
```

---

## Readiness Check (any time)

```bash
launchpad status --meta
launchpad status --repo kola-platform-core
```

Output:
```
status  →  apex-common/kola-meta

  [✔] Governance declared  (in governance-apex-common.yaml)
  [✔] Local clone          (~/Workspace/kola/kola-meta)
  [✔] Scaffold (meta)      (enabled)
  [✔] Harness pinned       (profile: meta-pm)

NEXT: launchpad status --meta
```

---

## Upgrading a Constitution (Rules)

Pin a new ref in `config/harness-apex-common.yaml`:

```yaml
profiles:
  python-backend:
    constitution:
      repo: python-services-rules
      ref: v2.2.0    # bumped from v2.1.0
```

Then re-run for each affected repo:

```bash
launchpad apply-harness --repo kola-platform-core --apply
launchpad status --repo kola-platform-core
```

---

## Further Reading

- [SCHEMA.md](SCHEMA.md) — 5 YAML kinds reference
- [stacks.md](stacks.md) — Adding custom stacks
- [kit-evolution.md](kit-evolution.md) — How the kit evolves across tenants
