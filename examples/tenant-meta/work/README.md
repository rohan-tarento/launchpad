# Work manifests

**PM does not author these for product INITs.** Dev generates content via `/spec-implementation-plan` §9 after Phase 2 merge (PRD + spec on `develop`).

Optional bulk board seed for **multi-repo** initiatives only. Copy §9 WorkManifest YAML from the dev implementation plan output. One file per initiative: `work/INIT-<id>.yaml`.

**Primary path (single repo):** dev runs `gh issue create` — one issue per wave (`W0`, `W1`, …). No file required in meta.

```bash
# After dev copies §9 to work/INIT-<id>.yaml
launchpad seed-work --config work/INIT-<id>.yaml --dry-run
launchpad seed-work --config work/INIT-<id>.yaml --apply
```

Playbook: [delivery-workflow.md](https://github.com/drivestream-lab/launchpad/blob/main/playbook/delivery-workflow.md#work-manifest) · [delivery-model.md](https://github.com/drivestream-lab/launchpad/blob/main/playbook/delivery-model.md)
