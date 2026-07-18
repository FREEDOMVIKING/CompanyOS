#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MODULES_DIR="$ROOT_DIR/companyos/modules"

if [ "$#" -eq 0 ]; then
    echo "Available modules:"
    echo

    for MODULE_DIR in "$MODULES_DIR"/*; do
        [ -d "$MODULE_DIR" ] || continue
        echo "  - $(basename "$MODULE_DIR")"
    done

    echo
    echo "Usage:"
    echo "  bash companyos/install_module.sh MODULE_NAME"
    exit 0
fi

MODULE_NAME="$1"
MODULE_DIR="$MODULES_DIR/$MODULE_NAME"
INSTALLER="$MODULE_DIR/install.sh"

if [ ! -d "$MODULE_DIR" ]; then
    echo "ERROR: Unknown module: $MODULE_NAME"
    exit 1
fi

if [ ! -f "$INSTALLER" ]; then
    echo "ERROR: Module installer is not ready:"
    echo "$INSTALLER"
    exit 1
fi

bash "$ROOT_DIR/companyos/backup.sh"
bash "$INSTALLER"
bash "$ROOT_DIR/companyos/verify.sh"

echo
echo "Module installed successfully: $MODULE_NAME"
