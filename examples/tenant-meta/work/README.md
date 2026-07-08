# Work manifests

`WorkManifest` YAML files drive backlog seeding onto a GitHub project board.

```bash
launchpad seed-work --config work/INIT-EXAMPLE-001.yaml --dry-run
launchpad seed-work --config work/INIT-EXAMPLE-001.yaml --apply
```

## When to use

After PRD sign-off, the dev team authors a `WorkManifest` (typically via the
`/spec-implementation-plan` agent skill in an app repo).  The PM reviews and
runs `seed-work` to create the issues and project items.

## Naming

`INIT-<id>.yaml` — one file per product initiative.  Use the same `initiative`
ID throughout (PRD, spec paths, branch names, issue titles).

## See also

- [playbook/sdd-workflow.md](../../playbook/sdd-workflow.md) — full SDD workflow
- [INIT-EXAMPLE-001.yaml](./INIT-EXAMPLE-001.yaml) — annotated example
