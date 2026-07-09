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
1.  Programme name?     → KOLA
2.  Programme slug?     → kola     (auto-derived; confirm or override)
3.  GitHub org?         → apex-common
4.  Workspace path?     → ~/Workspace/kola
```

Writes locally:

```
~/Workspace/kola/kola-meta/config/
  programme.yaml
  governance-apex-common.yaml      ← teams, repos, stack profiles
  harness-apex-common.yaml         ← constitution + skills pins (placeholders)
  scaffold-apex-common.yaml        ← cookiecutter templates (all disabled by default)
  service-catalog-apex-common.yaml ← service registry (commented examples)

~/.config/launchpad/clients.yaml      ← id: kola appended
~/.config/launchpad/env.d/kola.env ← GITHUB_TOKEN stub (chmod 600, fill in)
```

No GitHub API calls. No PAT required at this stage.

---

## After the interview

The wizard prints the exact **NEXT:** command to run. Follow it.

1. Open `~/.config/launchpad/env.d/kola.env` — paste your GitHub PAT.
2. Run `launchpad --client kola doctor` — confirms setup.
3. `launchpad init-client --meta --dry-run` then `--apply`.

Full walkthrough: **[greenfield.md](greenfield.md)**.

---

## Org ≠ slug pattern

GitHub org and programme slug are independent — e.g. org `apex-common`, slug `kola`, meta repo `kola-meta`.
See [examples/programme-kola.yaml](../examples/programme-kola.yaml) for a hand-authored `programme.yaml`.

---

## Related

- [greenfield.md](greenfield.md) — full Day-0 → Day-N guide
- [setup-guide.md](setup-guide.md) — phased setup reference
- [SCHEMA.md](SCHEMA.md) — 5 YAML kinds reference
