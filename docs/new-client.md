# New client onboarding

Workspace root: `/Users/kumar.deepak1/Workspace/handson/`

## 1. Create tenant meta repo

```bash
cp -r ~/Workspace/handson/launchpad/examples/tenant-meta \
      ~/Workspace/handson/<client>/<client>-meta
cd ~/Workspace/handson/<client>/<client>-meta
git init && git remote add origin <forge>/<client>-meta.git
```

## 2. Configure forge

Edit `scripts/config/*.yaml`:

- Replace `example-org` with your GitHub org or GitLab group
- Set repo list in `org-example.yaml` → rename to `org-<org>.yaml`
- Align `platform-`, `project-`, `gitflow-`, `verify-platform-`, `harness-` filenames with your org slug

## 3. Harness pins

In `harness-<org>.yaml`:

- `rules.repo` → **your private** `*-rules` repository
- `agent_skills.repo` → `drivestream-lab/prayog-skills` @ pinned tag

## 4. Secrets (per laptop)

```bash
mkdir -p ~/.config/launchpad/env.d
cat > ~/.config/launchpad/env.d/<client>.env <<'EOF'
export GITHUB_TOKEN=github_pat_...
export LAUNCHPAD_TENANT_ROOT=$HOME/Workspace/handson/<client>/<client>-meta
EOF
source ~/.config/launchpad/env.d/<client>.env
```

## 5. Bootstrap

```bash
launchpad doctor
launchpad setup --dry-run
launchpad setup --apply
```

## 6. First INIT

1. Draft PRD in `prd/INIT-….md` (prayog-skills in meta workspace)
2. Generate `work/INIT-….yaml`
3. `launchpad seed-work --config work/INIT-….yaml --apply`
4. Publish wiki: fill `wiki/` then push to forge wiki

## 7. App repos

```bash
launchpad sync-harness --repo <app> --apply
```

Clone app repos as siblings under `~/Workspace/handson/<client>/`.
