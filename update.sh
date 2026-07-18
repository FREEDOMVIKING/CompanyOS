#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RELEASES_DIR="$ROOT_DIR/companyos/releases"
LOG_FILE="$ROOT_DIR/companyos/logs/update_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================================================"
echo " CompanyOS Local Update"
echo "============================================================"

bash "$ROOT_DIR/companyos/backup.sh"

if [ "$#" -eq 0 ]; then
    echo
    echo "Usage:"
    echo "  bash companyos/update.sh path/to/release"
    echo
    echo "A release directory should contain install.sh."
    exit 0
fi

RELEASE_PATH="$1"

if [ ! -d "$RELEASE_PATH" ]; then
    echo "ERROR: Release directory was not found:"
    echo "$RELEASE_PATH"
    exit 1
fi

if [ ! -f "$RELEASE_PATH/install.sh" ]; then
    echo "ERROR: Release does not contain install.sh"
    exit 1
fi

echo
echo "Installing release:"
echo "$RELEASE_PATH"

bash "$RELEASE_PATH/install.sh"

echo
echo "Verifying updated system..."

if bash "$ROOT_DIR/companyos/verify.sh"; then
    echo
    echo "UPDATE INSTALLED SUCCESSFULLY"
else
    echo
    echo "UPDATE VERIFICATION FAILED"
    echo "Run this to restore the latest backup:"
    echo
    echo "  bash companyos/rollback.sh"
    exit 1
fi
