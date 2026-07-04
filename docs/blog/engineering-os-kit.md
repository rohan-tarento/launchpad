# We Didn't Need Better Agents. We Needed a Better Repo.

**A technical post on specification-driven development, harness engineering, and why we packaged our delivery model as a kit — not a platform.**

*Draft for Medium / technical blog. Review before publishing.*

---

## The scene

We had agents. We had Cursor. We had skills. We still had chaos.

Not because the models were weak — because **nothing in the repository told them what was true**. Product intent lived in one place. Implementation status lived in someone's head. Git policy lived in a Slack thread from six months ago. Every new initiative meant re-explaining the same rules to a fresh context window.

That was the real pain at Drivestream — and it's the pain we see again on every greenfield client and every brownfield rescue. The bottleneck isn't code generation. It's **repeatable truth** and **repeatable rails**.

We eventually packaged what we learned into **[Launchpad](https://github.com/drivestream-lab/launchpad)**: a public **kit** (CLI + playbook + tenant skeleton), not a SaaS. This post is the technical story behind it — what we productized, what we didn't, and what I'd do on Monday morning if I were starting a new customer engagement tomorrow.

---

## The mistake: bolting AI onto legacy layout

The default move in 2024–2025 is: add Copilot, add Cursor, add a skills folder, hope for the best.

That fails predictably:

| Symptom | Root cause |
|---------|------------|
| Agent "invents" APIs that don't exist | No **as-built** ground truth |
| PRs with no traceability | No **INIT** / spec path discipline |
| Policy drift between repos | Git rules in docs, not enforcement |
| Every laptop has a different agent setup | No **pinned** harness |
| PM and dev talk past each other | Two lanes, one Slack |

**Agents are compression algorithms for context.** If the context is scattered, the output is confident garbage.

The fix isn't a better prompt. It's an **engineering operating system**: where truth lives, how agents are constituted, and how git enforces the handoff.

---

## Pillar 1 — Specification-driven development (SDD)

We borrowed the name from spec-driven development, but tightened it for multi-repo, multi-agent work.

### Truth hierarchy (read in this order)

```text
1. Constitution     →  .cursor/rules/*.mdc  (private rules submodule)
2. Router           →  AGENTS.md
3. What to build    →  docs/specification/product/
4. Why              →  docs/specification/adr/
5. What is live     →  docs/specification/as-built/
```

The non-obvious bit is **#5**. Product specs describe intent. **As-built** describes reality. Agents (and humans) must not assume a feature exists because the product spec mentions it. Every serious change updates as-built in the **same PR** as code and tests.

### Two lanes, two repos types

```text
PM lane (<client>-meta)              Dev lane (app repos)
────────────────────────             ────────────────────
prd/          INIT PRDs              docs/specification/product/
work/         seed manifests         docs/specification/as-built/
planning/     pre-build archive      docs/specification/adr/
config/  factory YAML          code + tests/verify/
```

**Meta** holds narrative and factory config. **App repos** hold implementation truth. Long-form pre-build planning stays in meta — not as aspirational docs scattered across microservices.

### PR traceability (non-negotiable)

Every implementation PR carries:

- **Initiative** — e.g. `INIT-EXAMPLE-002`
- **Issue #**
- **Spec paths touched**
- **Verify command run**

Without that, the board is theatre.

---

## Pillar 2 — Harness engineering

If SDD answers *what*, harness answers *how the agent is allowed to behave*.

### The harness is a frozen surface

Each app repo gets a **pin file** at the root:

```yaml
# .harness-pin.yaml (conceptual)
profile: python-backend

rules:
  repo: your-org/service-rules   # private — MDC constitution
  ref: v1.0.0

agent_skills:
  repo: drivestream-lab/prayog-skills
  ref: v0.3.1
  skills:
    - spec-feasibility-review
    - spec-implementation-plan
    - pre-implement
    - verify
```

**Rules** stay private per customer — they're your constitution, not ours to ship. **Skills** come from public [prayog-skills](https://github.com/drivestream-lab/prayog-skills) — the dev workflow bundle (`/pre-implement`, `/verify`, etc.).

`sync-harness-app` writes the pin, `AGENTS.md`, the rules submodule, and seeds skills into `.agents/skills/` (gitignored; reproducible from the pin). `verify-harness-app` checks the repo still matches tenant config.

### PM skills vs dev skills (don't mix lanes)

| Where | Skills | Examples |
|-------|--------|----------|
| **`<client>-meta`** | PM pipeline | `/prd`, `/validate-requirements`, `/prd-impact-map` |
| **App repos** | Dev bundle | `/spec-feasibility-review`, `/pre-implement`, `/verify` |

PM skills install in the meta workspace. Dev skills arrive via harness sync. Collapsing those lanes is how you get PM validation running against the wrong tree.

---

## Pillar 3 — Factory (enforcement, not documentation)

Docs alone lose to deadline pressure. We automate the boring enforcement:

| Mechanism | What it enforces |
|-----------|------------------|
| **Teams + branch protection** | Who merges `develop` vs `main` |
| **Gitflow YAML** | Branch naming, merge policy, PR rules, CI gates |
| **Rulesets + workflows** | `policy-branch-name`, `policy-merge-source` |
| **Work manifests** | `seed-work` → epic + waves on the project board |

Critical design choice: **gitflow policy is YAML-authoritative**. The CLI does not take `--require-ci` or `--branch-naming` flags. You edit `gitflow-<org>.yaml`, PR it to meta, re-run `setup-gitflow --apply`. Policy changes are versioned like code.

Typical rollout:

```yaml
# Phase 1 — bootstrap
options:
  with_templates: true
  branch_naming: true
  require_ci: false

# Phase 2 — after workflow PRs merge
options:
  require_ci: true
```

Factory is GitHub-first today; GitLab covers `seed-work` + labels. Honest scope beats fake parity.

---

## How it fits together

```text
                    ┌─────────────────┐
                    │  launchpad kit  │
                    │ CLI + playbook  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   <client>-meta         app repos          private rules
   PRDs, manifests      specs, code        *.mdc constitution
   factory YAML         harness pin
         │                   │
         └──── seed-work ────┘
                    │
                    ▼
              GitHub board
         (INIT, codebase, verify cmd)
```

The **kit** (`launchpad` repo) never contains customer PRDs or private rules. The **tenant** (`<client>-meta`) does. You install Launchpad once per machine; you copy [`examples/tenant-meta`](https://github.com/drivestream-lab/launchpad/tree/main/examples/tenant-meta) per customer.

---

## Greenfield vs brownfield

| | Greenfield | Brownfield |
|---|------------|------------|
| **Fit** | Strong — you're installing the OS | Partial — you're retrofitting rails |
| **Meta** | Copy skeleton, rename org | Often exists; add factory YAML + playbook |
| **App repos** | `bootstrap-org` creates them | Already exist; `sync-harness-app` + spec layout graft |
| **Git policy** | `setup-gitflow --apply` | Same, but team habits lag enforcement |
| **Spec debt** | Low if you start with SDD | High — as-built backfill is manual |

Launchpad **productizes the pattern**. It does not auto-migrate ten years of tribal knowledge. Brownfield success still needs a spec audit, harness retrofit, and patience.

---

## What we deliberately did *not* build

Calling it a **kit** is intentional:

- **Not a SaaS** — no hosted tenant, no vendor lock-in
- **Not rules in the public repo** — constitution stays `your-org/*-rules`, pinned per app
- **Not "push button client"** — people still join teams in GitHub UI; meta is pushed manually first
- **Not full GitLab factory** — yet
- **Not magic brownfield** — migration is playbook + discipline

That's the right trade for a consultancy / platform team: ship **repeatable scaffolding**, keep **customer-specific truth private**.

---

## Monday-morning checklist (new customer)

If this post is useful, here's the compressed runbook:

1. **Clone Launchpad** — `pip install -e .` or `bin/launchpad` from source
2. **Copy `examples/tenant-meta`** → `~/Workspace/handson/<client>/<client>-meta`
3. **Edit `config/*.yaml`** — org, repos, gitflow, harness, project
4. **Push meta** — factory doesn't create your meta repo
5. **`launchpad setup-platform --apply`** — repos, teams, gitflow, board
6. **Clone app repos as siblings** → **`launchpad sync-harness-app --repo <app> --apply`**
7. **First INIT** — PRD in `prd/`, manifest in `work/`, `seed-work --apply`
8. **Dev** — spec handoff PRs, then `feature/INIT-*` implementation PRs with verify

Full walkthrough: [setup-guide.md](https://github.com/drivestream-lab/launchpad/blob/main/docs/setup-guide.md) in the repo.

---

## Takeaways

1. **Agents amplify repo design.** Bad layout → bad outcomes at scale.
2. **SDD separates intent (`product/`) from reality (`as-built/`).** Skipping as-built is how agents hallucinate features.
3. **Harness engineering pins constitution + skills.** Reproducibility beats "works on my laptop."
4. **Factory automation makes policy cheap to replay** — YAML gitflow, manifests, board fields.
5. **Ship a kit, not a platform** — institutional memory you copy per customer beats a monolith nobody owns.

---

## What's next

We're using Launchpad on new engagements and converging brownfield repos toward the same layout. Likely follow-ups:

- Brownfield migration playbook (spec audit, incremental gitflow)
- GitLab factory parity
- Stronger verify hooks between `verify-platform` and `seed-work`

If you're building multi-client agent-assisted delivery, steal the pattern. The repos are public:

- **Kit:** [github.com/drivestream-lab/launchpad](https://github.com/drivestream-lab/launchpad)
- **Skills:** [github.com/drivestream-lab/prayog-skills](https://github.com/drivestream-lab/prayog-skills)

---

*Questions or war stories welcome — especially brownfield retrofits where spec debt met an agent for the first time.*
