#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUPS_DIR="$ROOT_DIR/companyos/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DESTINATION="$BACKUPS_DIR/manual_$TIMESTAMP"

mkdir -p "$DESTINATION"

echo "Creating backup: $DESTINATION"

for ITEM in \
    company_cycle.py \
    company_manager.py \
    ceo_company.py \
    agents \
    ceo_memory \
    company_builds \
    companyos/version.json \
    companyos/manifest.json
do
    if [ -e "$ROOT_DIR/$ITEM" ]; then
        mkdir -p "$DESTINATION/$(dirname "$ITEM")"
        cp -a "$ROOT_DIR/$ITEM" "$DESTINATION/$ITEM"
    fi
done

echo "$DESTINATION" > "$ROOT_DIR/companyos/latest_backup.txt"

echo "Backup complete."
echo "$DESTINATION"
