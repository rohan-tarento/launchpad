# Greenfield app repo onboarding

Repeatable sequence for a **new application repository** (Python backend today; Next.js BFF planned): factory repo on GitHub → foundation code → gitflow → harness envelope → SDD handoff → wave PRs.

Run commands from **`<client>-meta`** unless noted. Default is **`--dry-run`**; pass **`--apply`** to write or call GitHub.

---

## Mental model

Three layers — do not skip or reorder:

```text
┌──────────────────────────────────────────────────────────────┐
│ Meta (SSOT)     harness + org + gitflow YAML already describe │
│                 the repo before it exists on disk             │
├──────────────────────────────────────────────────────────────┤
│ 1. bootstrap-org          empty GitHub repo (if missing)        │
│ 2. launchpad scaffold     cookiecutter foundation CODE        │
│ 3. git push develop       remote has content                  │
│ 4. setup-gitflow          branch policy + CI templates        │
│ 5. sync-harness           rules + skills + AGENTS.md          │
│ 6. verify-harness         pins match meta                     │
├──────────────────────────────────────────────────────────────┤
│ 7. spec handoff PR        docs/specification/product/INIT-*   │
│ 8. wave PRs (W0…)         business logic on top of foundation │
└──────────────────────────────────────────────────────────────┘
```

**Harness config in meta** is not the same as **sync-harness on the app repo**:

| | Harness YAML in meta | `sync-harness-app` on app repo |
|--|---------------------|----------------------------|
| When | Before or during planning | After local app folder exists |
| What | Declares profile, scaffold options, pin templates | Writes submodules, `.harness-pin.yaml`, `AGENTS.md` |

**Scaffold before sync-harness** — sync needs a directory to write into.

---

## Prerequisites

- [ ] `launchpad` installed (`pipx install …`, `launchpad --version`)
- [ ] Client registry + token: `~/.config/launchpad/clients.yaml`, `env.d/<client>.env`
- [ ] `launchpad doctor` clean from meta
- [ ] Repo listed in `config/org-<org>.yaml` and `config/harness-<org>.yaml`
- [ ] For Python: [python-fastapi-foundation](https://github.com/example-org/python-fastapi-foundation) reachable (local sibling or `LAUNCHPAD_PYTHON_FOUNDATION` or `gh:` URL after publish)
- [ ] GitHub HTTPS auth: `gh auth login` or PAT with `repo` scope (`git config --global credential.helper` / osxkeychain)

---

## Step 0 — Register repo in meta (once per app)

### Org config

Ensure repo name appears under `config/org-<org>.yaml` `repos:` (usually done via `bootstrap-org` or manual edit).

### Harness config

Add under `config/harness-<org>.yaml`:

```yaml
repos:
  example-api:
    profile: python-backend          # harness + scaffold profile (same name)
    service_name: Example API        # human label → service_description
    conda_env: example-api           # local verify env name
    verify_smoke: make test
    scaffold:                        # cookiecutter options (optional overrides)
      has_postgres: "yes"
      has_redis: "yes"               # omit → profile default is also "yes"
      has_kafka: "yes"
      has_internal_api: "yes"        # before W1 if E1 uses /internal/v1/…
```

**Profile defaults** (launchpad `python-backend`) apply for keys not listed under `scaffold:`. Override only what differs from defaults.

### All `python-backend` cookiecutter options

| Scaffold key | Profile default | Generated when `yes` | When to override |
|--------------|-----------------|----------------------|------------------|
| `service_name` | *(from `--repo`)* | Package / folder name | — |
| `service_description` | *(from harness `service_name`)* | README / metadata | — |
| `default_port` | `8000` | Uvicorn port in config | Non-standard port |
| `auth_mode` | `jwt` | JWT Bearer middleware on `/api/v1` | `allowlist`, `mtls`, `none` |
| `has_postgres` | `yes` | SQLAlchemy async, Alembic, repositories | `no` for stateless APIs |
| `has_redis` | `yes` | Redis connection manager, settings, `docker-compose` Redis | `no` to slim W0 if no cache/rate-limit yet |
| `has_kafka` | `no` | Kafka consumer service + settings | `yes` for E2 / event ingress |
| `has_s3` | `no` | boto3 S3/CloudFront client | Object storage integrations |
| `has_cratedb` | `no` | CrateDB client | Manthan / data-platform style |
| `has_emqx` | `no` | EMQX REST publish service | MQTT telemetry publish |
| `has_telemetry` | `yes` | OpenTelemetry OTLP setup | `no` only for minimal spikes |
| `has_internal_api` | `no` | `/internal` router (service-to-service) | `yes` when peers call `/internal/v1/…` |

Values must be strings `"yes"` / `"no"` (cookiecutter choice format).

**Note:** Profile default includes Redis (`has_redis: yes`) so local `docker-compose` matches other python-backend repos; set `has_redis: "no"` under `scaffold:` only if you want a slimmer W0 skeleton.

Common overrides (quick reference):

| Scaffold key | Typical override | Example repos |
|--------------|------------------|---------------|
| `has_kafka` | `yes` | Event consumers, message ingress |
| `has_internal_api` | `yes` | Services with `/internal/v1/…` peers |
| `has_redis` | `no` | Minimal W0 with no cache yet |

Also add repo to `config/gitflow-<org>.yaml` if not already present.

Commit meta changes before scaffolding so `--repo` resolves scaffold context from harness.

---

## Step 1 — Verify platform (optional re-check)

```bash
cd <client>-meta
launchpad --client <client-id> verify-platform
```

Confirms org repos, teams, board, gitflow config are aligned.

---

## Step 2 — Create empty GitHub repo (if missing)

```bash
launchpad bootstrap-org --apply
# or limit debug: launchpad bootstrap-org --apply  # uses org YAML repos list
```

Confirm: `https://github.com/<org>/<repo>` exists (empty is fine).

---

## Step 2b — Seed branches and clone locally

After repos exist on GitHub, run from meta (or use `setup-platform --apply`, which includes these steps):

```bash
launchpad seed-repos --apply          # main + develop on GitHub; default branch develop
launchpad clone-repos --apply         # git clone develop into workspace parent
```

Layout (default `options.workspace: ..` in gitflow YAML):

```text
~/Workspace/<client>/
  <client>-meta/     # tenant meta (linked if created by onboard apply)
  example-api/       # app clone on develop
  example-registry/
```

If meta was scaffolded locally by `onboard apply` (files but no `.git`), `clone-repos` links the directory to the remote and merges `origin/develop`.

---

## Step 3 — Scaffold foundation code

### Path A — brand-new local folder (no clone yet)

Preview:

```bash
launchpad scaffold-app --repo example-api --dry-run
```

Generate into an empty path:

```bash
launchpad scaffold-app --repo example-api --apply
```

Then continue with **Step 4** (`git init`, first push).

### Path B — repo already on GitHub (recommended when remote exists)

Clone **`develop`** first (HTTPS), then **overlay** foundation files into that checkout. This preserves git history, remote, and any files not in the template (e.g. spec handoff docs).

```bash
cd ~/Workspace/<client>   # default_workspace parent

# fresh clone (remove local folder only if you want a clean checkout)
git clone -b develop https://github.com/example-org/example-api.git

cd <client>-meta
launchpad scaffold-app --repo example-api --dry-run --force
launchpad scaffold-app --repo example-api --apply --force
```

**`--force` does not delete the folder.** It generates the cookiecutter output in a temp directory and **merges** foundation files into the existing repo:

- **Overwrites** paths that exist in the template (e.g. `src/`, `Makefile`, `pyproject.toml`)
- **Preserves** `.git/`, remote, branch, and local-only files (e.g. `docs/specification/` not in template)

Skip **Step 4** `git init` if you cloned — go straight to review, commit, push:

```bash
cd ../example-api
git status
git add -A
git commit -m "chore: overlay python-fastapi-foundation scaffold"
git push
```

### Options

**One-shot** (generate + gitflow + harness) — Path A only, or after Path B overlay:

```bash
launchpad scaffold-app --repo example-api --apply --apply --force
```

CLI overrides (one-off): `--option has_kafka=yes` (repeatable).

If target exists without `--force`, scaffold errors — use **Path B** (`clone` + `--apply --force`) or pick another `--workspace`.

---

## Step 4 — First git commit and push (HTTPS, Path A only)

Skip this step if you used **Path B** (clone + overlay) — you already have `origin` and `develop`.

From the generated app directory:

```bash
cd ../example-api   # sibling of meta; adjust if default_workspace differs

git init
git checkout -b develop
git add .
git commit -m "chore: scaffold example-api from python-fastapi-foundation"

git remote add origin https://github.com/example-org/example-api.git
git push -u origin develop
```

Use **HTTPS** remotes consistently. Authenticate via `gh auth login` or a classic/fine-grained PAT when prompted.

---

## Step 5 — Gitflow on GitHub

From meta (after at least one push to `develop`):

```bash
cd <client>-meta
launchpad setup-gitflow --repo example-api --apply
```

Applies branch protection, merge policy, PR/issue templates, CI workflow stubs from `config/gitflow-<org>.yaml`.

---

## Step 6 — Harness sync and verify

```bash
launchpad sync-harness-app --repo example-api --apply
launchpad verify-harness-app --repo example-api
```

Commit harness artifacts in the app repo:

```bash
cd ../example-api
git add .
git commit -m "chore: sync harness pins"
git push
```

---

## Step 7 — Day-1 quality gate (app repo)

```bash
cd ../example-api
cp .env.example .env    # fill local secrets
make setup
make check
make test
```

---

## Step 8 — Product lane (not launchpad)

| Step | Owner | Action |
|------|-------|--------|
| Backlog | **Dev** | After spec PR merged: `gh issue create` per wave from §9, or copy §9 → `work/INIT-*.yaml` + `launchpad seed-work` (multi-repo) |
| Spec PR | **Dev** opens | PR: spec + feasibility + TDD + plan → `develop` |
| W0+ | Dev | Feature PRs on top of foundation (iac-local, adapters, domain code) |

See [delivery-workflow.md](delivery-workflow.md) and [delivery-model.md](delivery-model.md).

---

## Full cheat sheet (python-backend)

Replace `example-api`, `example-org`, and client id for each new repo.

### Path A — empty GitHub repo, first local checkout

```bash
cd ~/Workspace/<client>/<client>-meta
launchpad scaffold-app --repo example-api --apply

cd ../example-api
git init && git checkout -b develop
git add . && git commit -m "chore: scaffold example-api foundation"
git remote add origin https://github.com/example-org/example-api.git
git push -u origin develop
```

### Path B — remote repo exists (clone develop, overlay foundation)

```bash
cd ~/Workspace/<client>
git clone -b develop https://github.com/example-org/example-api.git

cd <client>-meta
launchpad scaffold-app --repo example-api --apply --force

cd ../example-api
git add -A && git commit -m "chore: overlay python-fastapi-foundation"
git push
```

### Factory envelope (both paths)

```bash
cd ~/Workspace/<client>/<client>-meta
launchpad setup-gitflow --repo example-api --apply
launchpad sync-harness-app --repo example-api --apply
launchpad verify-harness-app --repo example-api

# App repo — harness commit + dev setup
cd ../example-api
git add . && git commit -m "chore: sync harness pins" && git push
cp .env.example .env && make setup && make check && make test
```

---

## Onboarding checklist (copy per repo)

```markdown
- [ ] Repo in org YAML + harness YAML (+ gitflow YAML)
- [ ] harness `scaffold:` block reviewed for cookiecutter options
- [ ] `launchpad scaffold-app --repo <name> --dry-run` reviewed
- [ ] Path A: `launchpad scaffold-app --repo <name> --apply` **or** Path B: `git clone -b develop` then `--apply --force`
- [ ] `git push` to `https://github.com/<org>/<repo>.git` (develop)
- [ ] `launchpad setup-gitflow --repo <name> --apply` (issue templates + QA access via `defaults.grant_push`)
- [ ] `launchpad sync-harness-app --repo <name> --apply`
- [ ] `launchpad verify-harness-app --repo <name>`
- [ ] Harness commit pushed on app repo
- [ ] `make setup && make check && make test` green
- [ ] Spec handoff PR merged
- [ ] W0 wave PR opened
```

---

## Profiles (extensible)

| Harness / scaffold profile | Template | Status |
|----------------------------|----------|--------|
| `python-backend` | `python-fastapi-foundation` | Implemented |
| `frontend` (`nextjs-bff` alias) | `nextjs-bff-foundation` (planned) | Stub |

Same command shape when frontend lands: `launchpad scaffold-app --repo example-ops` with `profile: frontend` in harness.

---

## Related

- [harness-pins.md](harness-pins.md) — pin file and sync-harness details
- [python-automation.md](python-automation.md) — full CLI reference
- [docs/SCHEMA.md](../docs/SCHEMA.md) — `HarnessConfig` and `scaffold:` overrides
- [python-fastapi-foundation](https://github.com/example-org/python-fastapi-foundation) — cookiecutter option reference
