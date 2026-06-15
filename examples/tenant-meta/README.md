# Example tenant meta

Copy this tree to start a new client workspace under your handson root:

```bash
cp -r examples/tenant-meta ~/Workspace/handson/<client>/<client>-meta
cd ~/Workspace/handson/<client>/<client>-meta
```

1. Rename `example-org` → your forge org/group in `scripts/config/*.yaml`
2. Set harness pins to **your private** `*-rules` repos + [prayog-skills](https://github.com/drivestream-lab/prayog-skills)
3. `cp .env.example .env` and set `GITHUB_TOKEN` or `GITLAB_TOKEN`
4. `launchpad doctor`
5. `launchpad setup --apply` (after dry-run)

See [docs/new-client.md](../../docs/new-client.md).
