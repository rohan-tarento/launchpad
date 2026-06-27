# Example tenant meta

**Single tenant skeleton** for Launchpad — copy once per client, then rename org/repos in `scripts/config/`.

```bash
cp -r examples/tenant-meta ~/Workspace/handson/<client>/<client>-meta
cd ~/Workspace/handson/<client>/<client>-meta
```

1. Replace `example-org` with your forge org in all `scripts/config/*.yaml`
2. Rename config files to match your org slug (e.g. `org-kd_diet_coke.yaml`, `platform-kd_diet_coke.yaml`)
3. Set harness pins to **your private** `*-rules` repo + [prayog-skills](https://github.com/drivestream-lab/prayog-skills)
4. Register the tenant on your machine — [multi-laptop.md](../../docs/multi-laptop.md):

```bash
# ~/.config/launchpad/clients.yaml — add path to this repo
# ~/.config/launchpad/env.d/<client-id>.env — GITHUB_TOKEN
launchpad doctor
```

5. `launchpad setup-platform --config scripts/config/platform-<org>.yaml --dry-run` then `--apply`

**Local smoke** (no PAT): from launchpad repo root, `./scripts/smoke-local.sh` uses this tree via `LAUNCHPAD_TENANT_ROOT`.

Full walkthrough: [docs/setup-guide.md](../../docs/setup-guide.md) · checklist: [docs/new-client.md](../../docs/new-client.md).

**No `.env` in meta** — factory secrets live in `~/.config/launchpad/env.d/` only.
