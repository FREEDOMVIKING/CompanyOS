#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/system_check_v1_$STAMP"

echo "=== CompanyOS System Check V2 Patch ==="
[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts"

if [ -f "$ROOT/scripts/full_system_check.py" ]; then
  cp "$ROOT/scripts/full_system_check.py" "$BACKUP/full_system_check.py"
fi

cp "$HERE/scripts/full_system_check.py" "$ROOT/scripts/full_system_check.py"
chmod +x "$ROOT/scripts/full_system_check.py"

cd "$ROOT"
if [ -d "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

COMPANYOS_ROOT="$ROOT" python "$ROOT/scripts/full_system_check.py"
