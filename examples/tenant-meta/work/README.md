# Work manifests (`work/`)

`WorkManifest` YAML files document epic + wave structure for an INIT. They are **archived in meta for traceability** — not consumed by a factory CLI in v0.5.10.

## Board seeding (v0.5.10)

After spec PR merge, dev seeds the board with **`gh issue create` per wave** from `/spec-implementation-plan` §9:

```bash
# Example — one issue per wave (titles/bodies from plan §9)
gh issue create --title "[INIT-EXAMPLE-001 W0] ..." --body-file w0-body.md --label initiative
```

See [playbook/delivery-workflow.md](../../playbook/delivery-workflow.md).

## Archive format

`INIT-EXAMPLE-001.yaml` is a **synthetic example** of the WorkManifest shape. Dev may copy §9 into `work/INIT-*.yaml` and open a meta PR for audit trail; PM merges when present.
