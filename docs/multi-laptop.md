# Multi-laptop setup

## Install launchpad once per machine

```bash
cd ~/Workspace/handson/launchpad
pipx install -e .
```

## Client index (private to you)

Optional `~/.config/launchpad/clients.yaml`:

```yaml
clients:
  - id: acme
    path: ~/Workspace/handson/acme/acme-meta
    forge: github
  - id: globex
    path: ~/Workspace/handson/globex/globex-meta
    forge: gitlab
```

## Per-client env files

```text
~/.config/launchpad/env.d/
  acme.env
  globex.env
```

## Verify

```bash
source ~/.config/launchpad/env.d/acme.env
cd ~/Workspace/handson/acme/acme-meta
launchpad doctor
```

## Pin versions

Tenant `.launchpad-version` should match `pipx list | grep launchpad`.
