# Example tenant meta (smoke fixture)

**Greenfield:** `launchpad onboard apply` renders `config/*.yaml` and `templates/` only. Layout stubs (`prd/`, `work/`, …) come from **`launchpad scaffold-meta --apply --force`** ([tenant-meta-foundation](https://github.com/drivestream-lab/tenant-meta-foundation)).

Clone the foundation locally (lab layout):

```bash
git clone https://github.com/drivestream-lab/tenant-meta-foundation.git \
  ~/Workspace/handson/drivestream-lab/tenant-meta-foundation
```

Or set `LAUNCHPAD_META_FOUNDATION` to your clone path.

This tree remains for **local smoke** (`LAUNCHPAD_TENANT_ROOT=examples/tenant-meta`, `./scripts/smoke-local.sh`).

Full walkthrough: [docs/setup-guide.md](../../docs/setup-guide.md) · checklist: [docs/new-client.md](../../docs/new-client.md).

**No `.env` in meta** — factory secrets live in `~/.config/launchpad/env.d/` only.
