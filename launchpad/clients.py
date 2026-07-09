"""Client registry — ~/.config/launchpad/clients.yaml is SSOT.

Resolution order (first match wins):
  1. explicit --client <id> flag
  2. LAUNCHPAD_CLIENT env var  (CI / scripting use)
  3. default: key in clients.yaml
  4. auto-pick if only one client is registered

If none match, commands that need a client raise ClientRegistryError with
a clear message pointing to clients.yaml.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path.home() / ".config" / "launchpad"
CLIENTS_FILE = CONFIG_DIR / "clients.yaml"
ENV_D_DIR = CONFIG_DIR / "env.d"


class ClientRegistryError(RuntimeError):
    pass


def _load_dotenv_file(path: Path) -> None:
    if not path.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=False)
    except ImportError:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


def load_clients_registry() -> dict[str, Any]:
    """Load ~/.config/launchpad/clients.yaml. Returns empty dict if missing."""
    if not CLIENTS_FILE.is_file():
        return {}
    with CLIENTS_FILE.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ClientRegistryError(f"expected mapping in {CLIENTS_FILE}")
    return data


def list_clients() -> list[dict[str, Any]]:
    registry = load_clients_registry()
    clients = registry.get("clients") or []
    if not isinstance(clients, list):
        raise ClientRegistryError(f"clients must be a list in {CLIENTS_FILE}")
    out: list[dict[str, Any]] = []
    for item in clients:
        if isinstance(item, dict) and item.get("id"):
            out.append(
                {
                    "id": str(item["id"]),
                    "path": str(item.get("path", "")),
                    "forge": str(item.get("forge", "")),
                }
            )
    return out


def _client_by_id(client_id: str) -> dict[str, Any] | None:
    for client in list_clients():
        if client["id"] == client_id:
            return client
    return None


def resolve_client_path(client_id: str) -> Path:
    client = _client_by_id(client_id)
    if not client:
        known = ", ".join(c["id"] for c in list_clients()) or "(none)"
        raise ClientRegistryError(
            f"unknown client {client_id!r} — known: {known}. "
            f"Edit {CLIENTS_FILE}"
        )
    raw_path = client.get("path", "").strip()
    if not raw_path:
        raise ClientRegistryError(f"client {client_id!r} missing path in {CLIENTS_FILE}")
    path = Path(raw_path).expanduser().resolve()
    if not path.is_dir():
        raise ClientRegistryError(
            f"client {client_id!r} path is not a directory: {path}"
        )
    return path


def resolve_client_id(explicit: str = "") -> str | None:
    """Pick active client: explicit flag/env → registry default → sole client."""
    if explicit.strip():
        return explicit.strip()

    env_client = os.environ.get("LAUNCHPAD_CLIENT", "").strip()
    if env_client:
        return env_client

    registry = load_clients_registry()
    default = str(registry.get("default", "")).strip()
    if default:
        return default

    clients = list_clients()
    if len(clients) == 1:
        return clients[0]["id"]

    return None


def load_client_env(client_id: str) -> Path | None:
    """Load secrets from ~/.config/launchpad/env.d/<client_id>.env."""
    env_file = ENV_D_DIR / f"{client_id}.env"
    if env_file.is_file():
        _load_dotenv_file(env_file)
        return env_file
    return None


def apply_client_context(explicit_client: str = "") -> str | None:
    """Resolve client, inject secrets from env.d, export LAUNCHPAD_CLIENT.

    Returns the resolved client_id, or None if no client could be derived.
    Callers that require a client should check for None and raise an error.
    """
    client_id = resolve_client_id(explicit_client)
    if not client_id:
        return None

    os.environ["LAUNCHPAD_CLIENT"] = client_id
    load_client_env(client_id)
    return client_id


def config_dir_for_client(client_id: str) -> "Path":
    """Return the config/ directory for a resolved client_id.

    Derives the path from clients.yaml — no LAUNCHPAD_TENANT_ROOT needed.
    """
    return resolve_client_path(client_id) / "config"


def format_clients_table() -> str:
    registry = load_clients_registry()
    default = str(registry.get("default", "")).strip()
    clients = list_clients()
    if not clients:
        return (
            f"No clients configured.\n"
            f"Create {CLIENTS_FILE} — see docs/multi-laptop.md"
        )

    lines = ["Configured clients:", ""]
    for client in clients:
        marker = " (default)" if client["id"] == default else ""
        forge = f" [{client['forge']}]" if client.get("forge") else ""
        env_file = ENV_D_DIR / f"{client['id']}.env"
        secrets = "secrets: yes" if env_file.is_file() else "secrets: no env.d file"
        lines.append(f"  {client['id']}{marker}{forge}")
        lines.append(f"    path: {client['path']}")
        lines.append(f"    {secrets}")
        lines.append("")
    lines.append(f"Registry: {CLIENTS_FILE}")
    lines.append(f"Secrets:  {ENV_D_DIR}/<id>.env")
    return "\n".join(lines)
