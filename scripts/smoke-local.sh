#!/usr/bin/env bash
# Local smoke test — no PAT required (dry-run only).
# Uses examples/tenant-meta as LAUNCHPAD_TENANT_ROOT.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TENANT="${ROOT}/examples/tenant-meta"
CFG="${TENANT}/config"

export LAUNCHPAD_TENANT_ROOT="${TENANT}"

echo "=== launchpad local smoke (v0.5.10) ==="

"${ROOT}/bin/launchpad" --version
"${ROOT}/bin/launchpad" --help >/dev/null
"${ROOT}/bin/launchpad" doctor || true

# Schema validation smoke — dry-run init-client against example config
"${ROOT}/bin/launchpad" init-client --meta \
  --config-dir "${CFG}" \
  --dry-run

# Status smoke
"${ROOT}/bin/launchpad" status --meta \
  --config-dir "${CFG}" || true  # exits 1 if not all checks pass — expected in smoke

echo "=== smoke OK ==="
