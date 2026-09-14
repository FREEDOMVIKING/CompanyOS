#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${HOME}/companyos"
BOOT_DIR="${HOME}/.termux/boot"
BOOT_FILE="${BOOT_DIR}/start-companyos"
mkdir -p "$BOOT_DIR"
cat > "$BOOT_FILE" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
cd "$ROOT"
mkdir -p "$ROOT/.companyos_runtime"
"$ROOT/scripts/companyosctl" recover >> "$ROOT/.companyos_runtime/termux_boot.log" 2>&1
EOF
chmod +x "$BOOT_FILE"
echo "Installed: $BOOT_FILE"
echo "Termux:Boot Android add-on is required for Android boot execution."
