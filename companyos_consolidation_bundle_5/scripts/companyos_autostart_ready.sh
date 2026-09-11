#!/data/data/com.termux/files/usr/bin/bash
# Autostart-ready launcher only.
# This file is NOT installed into ~/.termux/boot automatically by Bundle 5.
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
cd "$ROOT" || exit 1
exec bash "$ROOT/scripts/companyos_service.sh" start
