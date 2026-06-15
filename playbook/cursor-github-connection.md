# Cursor ↔ GitHub (example-org)

Connect your GitHub account for **example-org** repos used in Example bootstrap and development.

---

## 1. Integrations

| Integration | Purpose |
|-------------|---------|
| **Git clone / push** | Local work against `example-org/*` remotes |
| **Cursor built-in Git** | Diff, commit, PR from IDE |
| **GitHub CLI (`gh`)** | Day-to-day PRs; optional alongside factory PAT |
| **Factory PAT** | `launchpad` only — see [python-automation.md](python-automation.md) |

---

## 2. GitHub CLI

```bash
gh auth login
gh config set git_protocol https
gh auth status
gh org list                    # includes example-org
gh repo list example-org
```

Use fully qualified repos in scripts:

```bash
gh repo view example-org/<client>-meta
gh repo view example-org/example-api
```

---

## 3. Cursor

1. Open workspace folder containing **<client>-meta** and **example-api** (sibling clones under your handson path).
2. Cursor Settings → **Git** — ensure repo is detected.
3. Optional: Cursor Dashboard → Integrations → GitHub — grant **example-org** repos you use daily.

Factory automation uses **`GITHUB_TOKEN` in <client>-meta/.env`** — separate from `gh auth` unless you export the same token.

---

## 4. Multi-repo layout (recommended)

```text
~/Workspace/handson/drivestream/
  <client>-meta/    # playbook + launchpad
  example-api/            # Python pilot
```

Open **parent folder** or individual repos in Cursor as needed.

---

## Related

- [python-automation.md](python-automation.md)
- [bootstrap-prerequisites.md](bootstrap-prerequisites.md)
