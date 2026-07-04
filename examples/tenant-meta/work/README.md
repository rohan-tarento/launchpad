# Work manifests

Optional bulk board seed for **multi-repo** initiatives. Copy §9 WorkManifest YAML from `/spec-implementation-plan` output. One file per initiative: `work/INIT-<id>.yaml`.

Primary path (single repo): dev runs `gh issue create` — one issue per wave (`W0`, `W1`, …).

Run: `launchpad seed-work --config work/INIT-<id>.yaml --dry-run` then `--apply`.
