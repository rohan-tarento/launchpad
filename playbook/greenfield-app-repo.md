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

| | Harness YAML in meta | `sync-harness` on app repo |
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
- [ ] For Python: [python-fastapi-foundation](https://github.com/autrio10x/python-fastapi-foundation) reachable (local sibling or `LAUNCHPAD_PYTHON_FOUNDATION` or `gh:` URL after publish)
- [ ] GitHub HTTPS auth: `gh auth login` or PAT with `repo` scope (`git config --global credential.helper` / osxkeychain)

---

## Step 0 — Register repo in meta (once per app)

### Org config

Ensure repo name appears under `config/org-<org>.yaml` `repos:` (usually done via `bootstrap-org` or manual edit).

### Harness config

Add under `config/harness-<org>.yaml`:

```yaml
repos:
  suchana:
    profile: python-backend          # harness + scaffold profile (same name)
    service_name: Suchana            # human label → service_description
    conda_env: suchana               # local verify env name
    verify_smoke: make test
    scaffold:                        # cookiecutter options (optional overrides)
      has_postgres: "yes"
      has_redis: "yes"               # omit → profile default is also "yes"
      has_kafka: "yes"
      parichay_client: "yes"
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
| `parichay_client` | `yes` | HTTP client to Parichay | `no` if no auth integration |
| `abhilekh_client` | `no` | HTTP client to Abhilekh (device registry) | `yes` for device lookups |
| `kavach_client` | `no` | HTTP client to Kavach | Security/policy integrations |

Values must be strings `"yes"` / `"no"` (cookiecutter choice format).

**Suchana note:** P1 idempotency is **Postgres** (**D1**), not Redis. Redis cooldown / rule engine is later (**NG8**). Profile default still includes Redis (`has_redis: yes`) so local `docker-compose` matches other python-backend repos; set `has_redis: "no"` under `scaffold:` only if you want a slimmer W0 skeleton.

Common overrides (quick reference):

| Scaffold key | Typical override | Example repos |
|--------------|------------------|---------------|
| `has_kafka` | `yes` | Suchana, Pravah-style consumers |
| `has_internal_api` | `yes` | Suchana E1 (`/internal/v1/messages/…`) |
| `has_redis` | `no` | Minimal W0 with no cache yet |
| `abhilekh_client` | `yes` | Services needing device registry |

Also add repo to `config/gitflow-<org>.yaml` if not already present.

Commit meta changes before scaffolding so `--repo` resolves scaffold context from harness.

---

## Step 1 — Verify platform (optional re-check)

```bash
cd <client>-meta
launchpad --client drivestream verify-platform
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

## Step 3 — Scaffold foundation code

Preview (no writes):

```bash
launchpad scaffold --repo suchana --dry-run
```

Expect:

- `profile=python-backend` (inferred from harness — no need for `--profile` unless overriding)
- `template=…/python-fastapi-foundation`
- `output=<default_workspace>/<repo>` (usually sibling of meta)
- Cookiecutter context from profile defaults + `scaffold:` block

Generate:

```bash
launchpad scaffold --repo suchana --apply
```

**One-shot** (generate + gitflow + harness):

```bash
launchpad scaffold --repo suchana --apply --with-gitflow --with-harness
```

CLI overrides (one-off): `--option has_kafka=yes` (repeatable).

Fails if target directory already exists — remove or use `--workspace` for a different parent.

---

## Step 4 — First git commit and push (HTTPS)

From the generated app directory:

```bash
cd ../suchana   # sibling of meta; adjust if default_workspace differs

git init
git checkout -b develop
git add .
git commit -m "chore: scaffold suchana from python-fastapi-foundation"

git remote add origin https://github.com/autrio10x/suchana.git
git push -u origin develop
```

Use **HTTPS** remotes consistently. Authenticate via `gh auth login` or a classic/fine-grained PAT when prompted.

---

## Step 5 — Gitflow on GitHub

From meta (after at least one push to `develop`):

```bash
cd <client>-meta
launchpad setup-gitflow --repo suchana --apply
```

Applies branch protection, merge policy, PR/issue templates, CI workflow stubs from `config/gitflow-<org>.yaml`.

---

## Step 6 — Harness sync and verify

```bash
launchpad sync-harness --repo suchana --apply
launchpad verify-harness --repo suchana
```

Commit harness artifacts in the app repo:

```bash
cd ../suchana
git add .
git commit -m "chore: sync harness pins"
git push
```

---

## Step 7 — Day-1 quality gate (app repo)

```bash
cd ../suchana
cp .env.example .env    # fill local secrets
make setup
make check
make test
```

---

## Step 8 — Product lane (not launchpad)

| Step | Owner | Action |
|------|-------|--------|
| Backlog | PM | `launchpad seed-work --config work/INIT-*.yaml --apply` from meta |
| Spec handoff | PM/dev | PR: `docs/specification/product/INIT-*.md` → `develop` |
| W0+ | Dev | Feature PRs on top of foundation (iac-local, adapters, domain code) |

See [pm-dev-handoff.md](pm-dev-handoff.md) and [delivery-model.md](delivery-model.md).

---

## Full cheat sheet (python-backend)

Replace `suchana`, `autrio10x`, and client id for each new repo.

```bash
# Meta
cd ~/Workspace/handson/drivestream/drivestream-meta

launchpad --client drivestream scaffold --repo suchana --dry-run
launchpad --client drivestream scaffold --repo suchana --apply

# App repo — HTTPS
cd ../suchana
git init && git checkout -b develop
git add . && git commit -m "chore: scaffold suchana foundation"
git remote add origin https://github.com/autrio10x/suchana.git
git push -u origin develop

# Meta — factory envelope
cd ../drivestream-meta
launchpad setup-gitflow --repo suchana --apply
launchpad sync-harness --repo suchana --apply
launchpad verify-harness --repo suchana

# App repo — harness commit + dev setup
cd ../suchana
git add . && git commit -m "chore: sync harness pins" && git push
cp .env.example .env && make setup && make check && make test
```

---

## Onboarding checklist (copy per repo)

```markdown
- [ ] Repo in org YAML + harness YAML (+ gitflow YAML)
- [ ] harness `scaffold:` block reviewed for cookiecutter options
- [ ] `launchpad scaffold --repo <name> --dry-run` reviewed
- [ ] `launchpad scaffold --repo <name> --apply`
- [ ] `git push` to `https://github.com/<org>/<repo>.git` (develop)
- [ ] `launchpad setup-gitflow --repo <name> --apply`
- [ ] `launchpad sync-harness --repo <name> --apply`
- [ ] `launchpad verify-harness --repo <name>`
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

Same command shape when frontend lands: `launchpad scaffold --repo drivestream-ops` with `profile: frontend` in harness.

---

## Related

- [harness-pins.md](harness-pins.md) — pin file and sync-harness details
- [python-automation.md](python-automation.md) — full CLI reference
- [docs/SCHEMA.md](../docs/SCHEMA.md) — `HarnessConfig` and `scaffold:` overrides
- [python-fastapi-foundation](https://github.com/autrio10x/python-fastapi-foundation) — cookiecutter option reference
