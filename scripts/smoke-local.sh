#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TENANT="${ROOT}/examples/tenant-meta"
export LAUNCHPAD_TENANT_ROOT="${TENANT}"

echo "=== launchpad local smoke ==="
"${ROOT}/bin/launchpad" --help >/dev/null
"${ROOT}/bin/launchpad" doctor
"${ROOT}/bin/launchpad" seed-work --config work/INIT-EXAMPLE-001.yaml --dry-run
echo "=== smoke OK ==="
