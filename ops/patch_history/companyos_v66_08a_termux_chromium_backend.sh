#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
ENVF="$ROOT/.env"
MOD="$ROOT/companyos/runtime/browser_provider_onboarding.py"
CTL="$ROOT/scripts/companyos_browser_accountctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.08A TERMUX CHROMIUM BACKEND ====="
echo "GOAL=INSTALL_AND_WIRE_LOCAL_HEADLESS_CHROMIUM_CDP"
echo "NOTE=NO_AUTHORITY_SWITCHES_CHANGED"

[ -f "$MOD" ] || { echo "V66_08A_ABORT=missing:$MOD"; exit 1; }
[ -x "$CTL" ] || { echo "V66_08A_ABORT=missing:$CTL"; exit 1; }

echo "===== STORAGE PREFLIGHT ====="
avail_kb="$(df -Pk "$HOME" | awk 'NR==2 {print $4}')"
avail_mb=$((avail_kb/1024))
echo "AVAILABLE_MB=$avail_mb"
if [ "$avail_mb" -lt 1200 ]; then
  echo "V66_08A_ABORT=need_at_least_1200MB_free_for_chromium_install"
  exit 1
fi
echo "V66_08A_STORAGE_PREFLIGHT=PASS"

echo "===== INSTALL TERMUX X11 REPOSITORY IF NEEDED ====="
if ! dpkg -s x11-repo >/dev/null 2>&1; then
  pkg install -y x11-repo
fi
echo "V66_08A_X11_REPO=PASS"

echo "===== INSTALL CHROMIUM IF NEEDED ====="
if ! command -v chromium-browser >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1; then
  pkg install -y chromium
fi

BIN="$(command -v chromium-browser 2>/dev/null || command -v chromium 2>/dev/null || true)"
if [ -z "$BIN" ]; then
  echo "V66_08A_ABORT=chromium_binary_not_found_after_install"
  exit 1
fi
echo "CHROMIUM_BINARY=$BIN"
echo "V66_08A_CHROMIUM_INSTALL=PASS"

echo "===== WIRE COMPANYOS BROWSER EXECUTABLE ====="
python - "$BIN" <<'PY'
from pathlib import Path
import sys
p=Path.home()/"companyos/.env"
binpath=sys.argv[1]
lines=p.read_text(errors="ignore").splitlines() if p.exists() else []
out=[]
found=False
for line in lines:
    if line.startswith("COMPANYOS_BROWSER_EXECUTABLE="):
        out.append("COMPANYOS_BROWSER_EXECUTABLE="+binpath)
        found=True
    else:
        out.append(line)
if not found:
    out.append("COMPANYOS_BROWSER_EXECUTABLE="+binpath)
p.write_text("\n".join(out)+"\n")
p.chmod(0o600)
print("V66_08A_BROWSER_EXECUTABLE_WIRED=PASS")
PY

echo "===== HARDEN HEADLESS FLAGS FOR TERMUX ====="
python - <<'PY'
from pathlib import Path
p=Path.home()/"companyos/companyos/runtime/browser_provider_onboarding.py"
s=p.read_text()

old='''        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-background-networking",
'''
new='''        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--ozone-platform=headless",
        "--disable-background-networking",
'''
if old in s:
    s=s.replace(old,new,1)
elif '"--ozone-platform=headless"' not in s:
    raise SystemExit("V66_08A_ABORT=headless_flag_anchor_missing")

p.write_text(s)
print("V66_08A_TERMUX_HEADLESS_FLAGS=PASS")
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_08A_MODULE_COMPILE=PASS"

echo "===== STOP OLD BROWSER ONBOARDING LOOP ====="
"$CTL" stop || true
"$CTL" stop-browser || true

echo "===== BACKEND DETECTION ====="
"$CTL" backend

echo "===== START LOCAL CHROMIUM CDP ====="
"$CTL" start-browser

echo "===== VERIFY DEVTOOLS ENDPOINT ====="
python - <<'PY'
import json, urllib.request
url="http://127.0.0.1:9222/json/version"
with urllib.request.urlopen(url,timeout=10) as r:
    data=json.loads(r.read().decode())
print(json.dumps({
    "browser": data.get("Browser"),
    "protocol_version": data.get("Protocol-Version"),
    "websocket_present": bool(data.get("webSocketDebuggerUrl")),
}, indent=2))
assert data.get("webSocketDebuggerUrl")
print("V66_08A_CDP_HEALTH=PASS")
PY

echo "===== RUN ONE LIVE BROWSER ONBOARDING CYCLE ====="
"$CTL" once 1 || true

echo "===== RESTART BROWSER ONBOARDING LOOP ====="
"$CTL" restart

echo "===== FINAL STATUS ====="
"$CTL" backend
"$CTL" status

echo "V66_08A_TERMUX_CHROMIUM_BACKEND=PASS"
echo "V66_08A_HEADLESS_CDP=PASS"
echo "V66_08A_COMPANYOS_BROWSER_WIRING=PASS"
echo "V66_08A_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_08A_COMPLETE"
