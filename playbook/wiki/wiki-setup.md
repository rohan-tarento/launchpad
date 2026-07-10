# Wiki setup (required — BOOTSTRAP M4)

Wiki content is authored in **`wiki/`** in this repo and published to **<client>-meta** GitHub Wiki (git-backed).

**Rule:** Wiki = navigation + links. Commands and field tables stay in **playbook/**.

---

## One-time: enable wiki git remote

GitHub creates the `.wiki.git` repository only after the **first wiki page** exists.

1. Open tenant <client>-meta/wiki  
2. Click **Create the first page**  
3. Title: `Home`  
4. Body: paste from [`examples/tenant-meta/wiki/Home.md`](../../examples/tenant-meta/wiki/Home.md) or type one line and Save  
5. Close — the wiki git repo now exists

---

## Publish / update all pages

v0.5.10 has no `publish-wiki` CLI command. Publish manually via the wiki git remote:

```bash
cd /tmp
git clone https://github.com/<org>/<client>-meta.wiki.git
cd <client>-meta.wiki

# Copy pages from your meta repo checkout
cp ~/Workspace/<slug>/<client>-meta/wiki/*.md .

git add .
git commit -m "docs: sync wiki from wiki/"
git push origin master   # or main — GitHub wikis vary
```

Alternatively edit pages in the GitHub Wiki UI.

---

## Pages (must exist)

| Wiki page | Source file |
|-----------|-------------|
| Home | `wiki/Home.md` |
| Example-How-we-ship | `wiki/Example-How-we-ship.md` |
| Example-Python-dev | `wiki/Example-Python-dev.md` |
| Example-Platform-operator | `wiki/Example-Platform-operator.md` |
| Example-Skills-and-agents | `wiki/Example-Skills-and-agents.md` |

---

## Org wiki (optional mirror)

If you also use https://github.com/orgs/example-org/wiki — add the same five pages as **short link lists** pointing to:

- tenant <client>-meta/wiki

Do not maintain two bodies; **repo wiki + `wiki/` folder** is the publish path.

---

## After playbook edits

Wiki pages link into **playbook/** on `develop`. When playbook text changes:

```bash
git pull origin develop
# Re-publish wiki/*.md via wiki git clone (see above)
```

## Exit criteria (M4 Done)

- [ ] tenant <client>-meta/wiki shows Home + 4 child pages  
- [ ] Wiki git push succeeds (or pages updated in GitHub UI)  
- [ ] Board task **M4** → Done
