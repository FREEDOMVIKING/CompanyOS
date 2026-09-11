#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-$HOME/companyos}"
STAMP="$(date +%Y%m%d_%H%M%S)"

echo "============================================"
echo " COMPANYOS MASTER CONSOLIDATED INSTALLER"
echo "============================================"

if [ -d "$DEST" ]; then
  BACKUP="${DEST}_pre_master_${STAMP}"
  echo "Backing up current install to: $BACKUP"
  cp -a "$DEST" "$BACKUP"
fi

mkdir -p "$DEST"
cp -a "$SRC/." "$DEST/"

chmod +x "$DEST/scripts/"*.sh 2>/dev/null || true
chmod +x "$DEST/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$DEST:$DEST/src${PYTHONPATH:+:$PYTHONPATH}"

echo
echo "Running final verification..."
bash "$DEST/scripts/companyos_master_verify.sh"

echo
echo "============================================"
echo " COMPANYOS MASTER INSTALL COMPLETE"
echo " PHASE 16000 READY"
echo "============================================"
echo "Next commands:"
echo "bash $DEST/scripts/companyos_worker.sh drain"
echo "bash $DEST/scripts/companyos_daemon_control.sh start"
echo "bash $DEST/scripts/companyos_daemon_control.sh status"
