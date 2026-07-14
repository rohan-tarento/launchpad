#!/usr/bin/env bash
# Local smoke test — no PAT required (dry-run only).
# Uses examples/tenant-meta via --config-dir (no LAUNCHPAD_* env overrides).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TENANT="${ROOT}/examples/tenant-meta"
CFG="${TENANT}/config"

echo "=== launchpad local smoke ==="

"${ROOT}/bin/launchpad" --version
"${ROOT}/bin/launchpad" --help >/dev/null
"${ROOT}/bin/launchpad" doctor || true

# Schema validation smoke — dry-run init-client against example config
"${ROOT}/bin/launchpad" init-client --meta \
  --config-dir "${CFG}" \
  --dry-run

# Status smoke (workspace derived from --config-dir → parent of meta)
"${ROOT}/bin/launchpad" status --meta \
  --config-dir "${CFG}" || true  # exits 1 if not all checks pass — expected in smoke

echo "=== smoke OK ==="
