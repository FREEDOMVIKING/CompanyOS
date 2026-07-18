#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LATEST_FILE="$ROOT_DIR/companyos/latest_backup.txt"

if [ ! -f "$LATEST_FILE" ]; then
    echo "ERROR: No backup record was found."
    exit 1
fi

BACKUP_DIR="$(cat "$LATEST_FILE")"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "ERROR: Backup directory does not exist:"
    echo "$BACKUP_DIR"
    exit 1
fi

echo "============================================================"
echo " CompanyOS Rollback"
echo " Backup: $BACKUP_DIR"
echo "============================================================"

echo
echo "This will restore files from the latest backup."
echo "Current memory and code may be overwritten."
echo

read -r -p "Type RESTORE to continue: " CONFIRMATION

if [ "$CONFIRMATION" != "RESTORE" ]; then
    echo "Rollback cancelled."
    exit 0
fi

for ITEM in \
    company_cycle.py \
    company_manager.py \
    ceo_company.py \
    agents \
    ceo_memory \
    company_builds
do
    if [ -e "$BACKUP_DIR/$ITEM" ]; then
        rm -rf "$ROOT_DIR/$ITEM"
        cp -a "$BACKUP_DIR/$ITEM" "$ROOT_DIR/$ITEM"
        echo "Restored: $ITEM"
    fi
done

echo
echo "Running verification..."

bash "$ROOT_DIR/companyos/verify.sh"

echo
echo "Rollback completed successfully."
