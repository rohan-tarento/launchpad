# GitLab issue board (roadmap)

GitLab adapter is **phase 6**. Until then, use GitHub or manual GitLab setup with the same process discipline.

## Target mapping

| Launchpad field | GitLab equivalent |
|-----------------|-----------------|
| Status columns (7) | Scoped labels `status::backlog` … `status::done` |
| Codebase | Label `codebase::<repo>` |
| Initiative | Label `initiative::<INIT-id>` or milestone |
| Epic / tasks | Group epic + child issues (or parent/child) |
| `seed-work` | Create issues + labels via `python-gitlab` |

## Board

- **Group board** across client repos (closest to org-wide GitHub Project)
- Lists wired to status labels

See [docs/multi-forge.md](../docs/multi-forge.md).
