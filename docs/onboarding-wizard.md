# Onboarding wizard (v0.5.10)

> **tl;dr:** Run `launchpad onboard interview`. Answer 4 questions.
> All 5 config YAMLs, the client registry entry, and a PAT stub are written automatically.

---

## Command

```bash
launchpad onboard interview
```

`onboard interview` is the **only** public entry point for local setup.
There is no `onboard apply`, `onboard plan`, or `onboard show`.

---

## What happens

```
1.  Programme name?     → STRATUM
2.  Programme slug?     → stratum     (auto-derived; confirm or override)
3.  GitHub org?         → Sandvik-Common
4.  Workspace path?     → ~/Workspace/stratum
```

Writes locally:

```
~/Workspace/stratum/stratum-meta/config/
  programme.yaml
  governance-Sandvik-Common.yaml      ← teams, repos, stack profiles
  harness-Sandvik-Common.yaml         ← constitution + skills pins (placeholders)
  scaffold-Sandvik-Common.yaml        ← cookiecutter templates (all disabled by default)
  service-catalog-Sandvik-Common.yaml ← service registry (commented examples)

~/.config/launchpad/clients.yaml      ← id: stratum appended
~/.config/launchpad/env.d/stratum.env ← GITHUB_TOKEN stub (chmod 600, fill in)
```

No GitHub API calls. No PAT required at this stage.

---

## After the interview

The wizard prints the exact **NEXT:** command to run. Follow it.

1. Open `~/.config/launchpad/env.d/stratum.env` — paste your GitHub PAT.
2. Run `launchpad --client stratum doctor` — confirms setup.
3. `launchpad init-client --meta --dry-run` then `--apply`.

Full walkthrough: **[greenfield.md](greenfield.md)**.

---

## KOLA example (org ≠ slug)

Some programmes live inside a shared enterprise org:

| | |
|--|--|
| **GitHub org** | `apex-common` |
| **Programme slug** | `kola` |
| **Meta repo** | `kola-meta` |

```bash
mkdir -p ~/Workspace/kola && cd ~/Workspace/kola
launchpad onboard interview
# Programme name: KOLA
# Slug: kola
# GitHub org: apex-common
# Workspace: ~/Workspace/kola
```

See [examples/programme-kola.yaml](../examples/programme-kola.yaml) for the resulting `programme.yaml`.

---

## Related

- [greenfield.md](greenfield.md) — full Day-0 → Day-N guide
- [setup-guide.md](setup-guide.md) — phased setup reference
- [SCHEMA.md](SCHEMA.md) — 5 YAML kinds reference
