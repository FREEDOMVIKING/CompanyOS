#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
ENV_FILE="${HOME}/.companyos_launch_env"
BOOT_FILE="${HOME}/.termux/boot/start-companyos"

cd "$ROOT"

if [ ! -f ".companyos_runtime/full_autonomous_qualification.json" ]; then
  echo "ERROR: qualification file not found. Run the CompanyOS qualification first."
  exit 2
fi

python - <<'PY'
import json
from pathlib import Path
p = Path.home() / "companyos/.companyos_runtime/full_autonomous_qualification.json"
obj = json.loads(p.read_text())
if not obj.get("core_pass"):
    raise SystemExit("ERROR: core qualification is not passing.")
print("Core qualification: PASS")
print("Current launch level:", obj.get("launch_level"))
PY

tmp="$(mktemp)"
chmod 600 "$tmp"

cat > "$tmp" <<'EOF'
# CompanyOS launch environment
# Generated locally on this device. Do not commit this file.
EOF

ask_secret () {
  local var="$1"
  local label="$2"
  local val=""
  printf "%s (leave blank to skip): " "$label"
  IFS= read -r -s val
  echo
  if [ -n "$val" ]; then
    printf 'export %s=%q\n' "$var" "$val" >> "$tmp"
  fi
}

ask_text () {
  local var="$1"
  local label="$2"
  local default="${3:-}"
  local val=""
  if [ -n "$default" ]; then
    printf "%s [%s]: " "$label" "$default"
  else
    printf "%s (leave blank to skip): " "$label"
  fi
  IFS= read -r val
  if [ -z "$val" ] && [ -n "$default" ]; then
    val="$default"
  fi
  if [ -n "$val" ]; then
    printf 'export %s=%q\n' "$var" "$val" >> "$tmp"
  fi
}

echo
echo "===== OPENAI ====="
ask_secret OPENAI_API_KEY "OpenAI API key"

echo
echo "===== EMAIL / SMTP ====="
ask_text SMTP_HOST "SMTP host"
ask_text SMTP_PORT "SMTP port" "587"
ask_text SMTP_USERNAME "SMTP username"
ask_secret SMTP_PASSWORD "SMTP password/app password"
ask_text SMTP_FROM "SMTP from address"

echo
echo "===== HOSTING / VERCEL ====="
ask_secret VERCEL_TOKEN "Vercel token"

echo
echo "===== SOLANA / PHANTOM ====="
ask_text SOLANA_RPC_URL "Solana RPC URL"
ask_secret SOLANA_PRIVATE_KEY "Solana private key (base58/base64 as supported by your CompanyOS adapter)"

printf "Enable LIVE financial execution now? [y/N]: "
IFS= read -r live_finance
case "${live_finance:-N}" in
  y|Y|yes|YES)
    echo 'export COMPANYOS_ENABLE_LIVE_FINANCE=1' >> "$tmp"
    ;;
  *)
    echo 'export COMPANYOS_ENABLE_LIVE_FINANCE=0' >> "$tmp"
    ;;
esac

# Existing requested limits
echo 'export COMPANYOS_DAILY_FINANCE_CAP_USD=20000' >> "$tmp"
echo 'export COMPANYOS_SINGLE_FINANCE_CAP_USD=15000' >> "$tmp"
echo 'export COMPANYOS_MIN_TRANSACTION_AMOUNT=0.01' >> "$tmp"

mv "$tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# Ensure interactive shells load the launch environment.
PROFILE="${HOME}/.bashrc"
touch "$PROFILE"
if ! grep -Fq '.companyos_launch_env' "$PROFILE"; then
  cat >> "$PROFILE" <<'EOF'

# CompanyOS launch environment
if [ -f "$HOME/.companyos_launch_env" ]; then
  . "$HOME/.companyos_launch_env"
fi
EOF
fi

# Ensure Termux:Boot loads the same environment.
mkdir -p "${HOME}/.termux/boot"
cat > "$BOOT_FILE" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -e
if [ -f "$HOME/.companyos_launch_env" ]; then
  . "$HOME/.companyos_launch_env"
fi
cd "$HOME/companyos"
mkdir -p "$HOME/companyos/.companyos_runtime"
"$HOME/companyos/scripts/companyosctl" recover >> "$HOME/companyos/.companyos_runtime/termux_boot.log" 2>&1
EOF
chmod +x "$BOOT_FILE"

# Load into current shell for this launch.
set +u
. "$ENV_FILE"
set -u

echo
echo "===== CONNECTOR READINESS ====="
"$ROOT/scripts/companyos_connectorctl" || true

echo
echo "===== FINAL CORE QUALIFICATION ====="
"$ROOT/scripts/companyos_qualify"

echo
echo "===== START / RECOVER COMPANYOS ====="
"$ROOT/scripts/companyosctl" recover

echo
echo "===== FINAL HEALTH ====="
"$ROOT/scripts/companyosctl" health

echo
echo "===== DASHBOARD ====="
"$ROOT/scripts/companyos_dashboardctl" url

echo
echo "===== LAUNCH SUMMARY ====="
python - <<'PY'
import json
from pathlib import Path

root = Path.home() / "companyos"
q = json.loads((root / ".companyos_runtime/full_autonomous_qualification.json").read_text())
c = json.loads((root / ".companyos_runtime/connector_readiness.json").read_text())

print("core_pass:", q.get("core_pass"))
print("launch_level:", q.get("launch_level"))
print("connectors_configured:", c.get("configured_count"), "/", c.get("total_count"))
print("dashboard:", "http://127.0.0.1:8765/")
print("live_finance_enabled:",
      c.get("connectors", {}).get("solana_wallet", {}).get("live_finance_enabled"))
PY

echo
echo "COMPANYOS_FULL_LAUNCH_SETUP=COMPLETE"
echo
echo "Secrets were stored locally in:"
echo "  $ENV_FILE"
echo "Permissions:"
ls -l "$ENV_FILE"
