#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "=== CompanyOS Full System Check ==="
[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts"
cp "$HERE/scripts/full_system_check.py" "$ROOT/scripts/full_system_check.py"
chmod +x "$ROOT/scripts/full_system_check.py"

cd "$ROOT"

if [ -d "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT/src:$ROOT${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

COMPANYOS_ROOT="$ROOT" python "$ROOT/scripts/full_system_check.py"
