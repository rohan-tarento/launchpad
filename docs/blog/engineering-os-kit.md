# We Didn't Need Better Agents. We Needed a Better Repo.

> **Note:** This post was written during the pre-v0.5.10 era. Concepts below (SDD, harness, factory) still apply. **Commands and config layout changed in v0.5.10** — use [docs/greenfield.md](../greenfield.md) as the current runbook.
>
> | Pre-v0.5.10 (this post) | v0.5.10 (current) |
> |---------------------------|-------------------|
> | `onboard plan` / `onboard apply` | `onboard interview` |
> | `setup-platform`, `bootstrap-org`, `setup-gitflow` | `init-client --meta` / `--repo <name>` |
> | `scaffold-meta`, `scaffold-app` | `apply-scaffold --meta` / `--repo <name>` |
> | `sync-harness-app`, `check-harness` | `apply-harness`, `status` |
> | `seed-work` | `gh issue create` per wave from plan §9 |
> | `gitflow-<org>.yaml` | `governance-<org>.yaml` (+ 4 other YAML kinds) |

**A technical post on specification-driven development, harness engineering, and why we packaged our delivery model as a kit — not a platform.**

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
1. Constitution     →  .cursor/rules/*.mdc  (drivestream-lab/*-rules submodule)
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
# .harness-pin.yaml (python-backend example — refs from production harness)
profile: python-backend

rules:
  repo: drivestream-lab/python-services-rules
  ref: v0.5.5

agent_skills:
  repo: drivestream-lab/prayog-skills
  ref: v0.4.0
  skills:
    - spec-draft
    - initiative-feasibility
    - spec-technical-review
    - spec-implementation-plan
    - pre-implement
    - loop-spec
    - ground-spec
    - verify
```

**Rules** ship as public OSS per profile (`python-services-rules`, `data-platform-rules`, `nextjs-bff-rules`) — pinned per app. **Skills** come from public [prayog-skills](https://github.com/drivestream-lab/prayog-skills) — the eight-skill dev workflow bundle (`/spec-draft` through `/verify`).

Three layers stay separate: **MDC rules** = coding constitution; **`AGENTS.md`** = router (lists which skills); **`.agents/skills/`** = prayog procedures. Do not duplicate skill catalogs in rules repos — only the harness pin and `AGENTS.md` name them.

`apply-harness` writes the pin, the rules submodule, and seeds skills into `.agents/skills/` (reproducible from harness YAML). `status --repo` checks the repo still matches tenant config.

### PM skills vs dev skills (don't mix lanes)

| Where | Skills | Examples |
|-------|--------|----------|
| **`<client>-meta`** | PM pipeline | `/prd` (community), `/validate-requirements`, `/prd-impact-map` |
| **App repos** | Dev bundle | `/initiative-feasibility`, `/pre-implement`, `/verify` |

`/prd` comes from **awesome-copilot** (community skill), not prayog. PM skills install in the meta workspace. Dev skills arrive via harness sync. Collapsing those lanes is how you get PM validation running against the wrong tree.

---

## Pillar 3 — Factory (enforcement, not documentation)

Docs alone lose to deadline pressure. We automate the boring enforcement:

| Mechanism | What it enforces |
|-----------|------------------|
| **Teams + branch protection** | Who merges `develop` vs `main` |
| **Governance YAML** (`governance-<org>.yaml`) | Teams, repos, branch policy, project board |
| **Rulesets + workflows** | `policy-branch-name`, `policy-merge-source` (kit templates; manual deploy in v0.5.10) |
| **Board seeding** | `gh issue create` per wave from plan §9 |

Critical design choice: **policy is YAML-authoritative**. The CLI does not take `--require-ci` or `--branch-naming` flags. You edit `governance-<org>.yaml`, PR it to meta, re-run `init-client --apply`. Policy changes are versioned like code.

Factory is **GitHub-only** in v0.5.10. GitLab is planned (v0.6). Honest scope beats fake parity.

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
   <client>-meta         app repos          drivestream-lab rules
   PRDs, manifests      specs, code        *.mdc constitution
   factory YAML         harness pin
         │                   │
         └──── gh issue create ─┘
                    │
                    ▼
              GitHub board
         (INIT, codebase, verify cmd)
```

The **kit** (`launchpad` repo) never contains customer PRDs. **Rules** are public OSS in `drivestream-lab/*-rules`; the **tenant** (`<client>-meta`) holds factory config and PRDs. You install Launchpad once per machine via `pipx install` from a git tag, or run `launchpad onboard interview` for the guided Day-0 setup.

---

## Greenfield vs brownfield

| | Greenfield | Brownfield |
|---|------------|------------|
| **Fit** | Strong — you're installing the OS | Partial — you're retrofitting rails |
| **Meta** | `onboard interview` or copy skeleton | Often exists; add 5 YAML kinds + playbook |
| **App repos** | `init-client --repo` creates them | Already exist; `apply-harness` + spec layout graft |
| **Git policy** | `init-client --apply` | Same, but team habits lag enforcement |
| **Spec debt** | Low if you start with SDD | High — as-built backfill is manual |

Launchpad **productizes the pattern**. It does not auto-migrate ten years of tribal knowledge. Brownfield success still needs a spec audit, harness retrofit, and patience.

---

## What we deliberately did *not* build

Calling it a **kit** is intentional:

- **Not a SaaS** — no hosted tenant, no vendor lock-in
- **Not rules inside the launchpad repo** — constitution lives in public `drivestream-lab/*-rules`, pinned per app via submodule
- **Not "push button client"** — people still join teams in GitHub UI; meta is pushed manually first
- **Not full GitLab factory** — yet
- **Not magic brownfield** — migration is playbook + discipline

That's the right trade for a consultancy / platform team: ship **repeatable scaffolding**, keep **customer PRDs and factory config private** in `<client>-meta`.

---

## Monday-morning checklist (new customer — v0.5.10)

If this post is useful, here's the compressed runbook. Full detail: [greenfield.md](../greenfield.md).

1. **Install Launchpad** — `pipx install "launchpad @ git+https://github.com/drivestream-lab/launchpad@v0.5.13"`
2. **Day 0** — `launchpad onboard interview` (writes 5 YAMLs + client registry + PAT stub)
3. **Token** — set `GITHUB_TOKEN` in `~/.config/launchpad/env.d/<slug>.env`
4. **Day 1 meta** — `launchpad init-client --meta --apply`
5. **Scaffold + harness** — `apply-scaffold --meta --apply` (optional), `apply-harness --meta --apply`, `status --meta`
6. **Day N apps** — edit governance + scaffold YAMLs; `init-client --repo <name> --apply`, `apply-scaffold`, `apply-harness`
7. **First INIT** — PRD in `prd/`; dev seeds board with `gh issue create` per wave from plan §9
8. **Dev** — spec handoff PRs, then `feature/INIT-*` implementation PRs with verify

Full walkthrough: [setup-guide.md](../setup-guide.md) · [greenfield.md](../greenfield.md)

---

## Takeaways

1. **Agents amplify repo design.** Bad layout → bad outcomes at scale.
2. **SDD separates intent (`product/`) from reality (`as-built/`).** Skipping as-built is how agents hallucinate features.
3. **Harness engineering pins constitution + skills.** Reproducibility beats "works on my laptop."
4. **Factory automation makes policy cheap to replay** — YAML governance, board fields, harness pins.
5. **Ship a kit, not a platform** — institutional memory you copy per customer beats a monolith nobody owns.

---

## What's next

We're using Launchpad on new engagements and converging brownfield repos toward the same layout. Likely follow-ups:

- Brownfield migration playbook (spec audit, incremental governance)
- GitLab factory parity (v0.6)
- Bulk board seeding CLI (successor to legacy `seed-work`)

If you're building multi-client agent-assisted delivery, steal the pattern. The repos are public:

- **Kit:** [github.com/drivestream-lab/launchpad](https://github.com/drivestream-lab/launchpad)
- **Skills:** [github.com/drivestream-lab/prayog-skills](https://github.com/drivestream-lab/prayog-skills)
- **Rules:** [python-services-rules](https://github.com/drivestream-lab/python-services-rules) · [data-platform-rules](https://github.com/drivestream-lab/data-platform-rules) · [nextjs-bff-rules](https://github.com/drivestream-lab/nextjs-bff-rules)
- **Scaffolds:** [python-fastapi-foundation](https://github.com/drivestream-lab/python-fastapi-foundation) · [tenant-meta-foundation](https://github.com/drivestream-lab/tenant-meta-foundation)

---

*Questions or war stories welcome — especially brownfield retrofits where spec debt met an agent for the first time.*
