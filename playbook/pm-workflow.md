# PM workflow

> **Content moved to [pm-dev-handoff.md](pm-dev-handoff.md).**
>
> `pm-workflow.md` is retained for inbound links. All PM pipeline detail —
> skills install, three-phase timeline, seed-work gate, prompt templates —
> lives in `pm-dev-handoff.md`.

**Skills install (from `<client>-meta` root):**

```bash
npx skills add github/awesome-copilot --skill prd -a cursor -y
npx skills add drivestream-lab/prayog-skills --skill '*' -a cursor -y
npx skills list
```

**Full PM ↔ dev workflow:** [pm-dev-handoff.md](pm-dev-handoff.md)  
**Skills reference:** [skills-matrix.md](skills-matrix.md)  
**Board:** [github-project.md](github-project.md)
