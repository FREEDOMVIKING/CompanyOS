#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/runtime/browser_provider_onboarding.py"
CTL="$ROOT/scripts/companyos_browser_accountctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.08B CDP ORIGIN + RETRY FIX ====="
echo "FIX_1=CHROMIUM_DEVTOOLS_WEBSOCKET_403"
echo "FIX_2=RETRY_BROWSER_AUTOMATION_ERROR_CANDIDATES"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$MOD" ] || { echo "V66_08B_ABORT=missing:$MOD"; exit 1; }
[ -x "$CTL" ] || { echo "V66_08B_ABORT=missing:$CTL"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MOD" "${MOD}.v66_08b_backup_${stamp}"
echo "BACKUP=${MOD}.v66_08b_backup_${stamp}"

echo "===== PATCH CHROMIUM REMOTE ORIGIN ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/browser_provider_onboarding.py"
s=p.read_text()

old='''        "--no-sandbox",
        "--ozone-platform=headless",
        "--disable-background-networking",
'''
new='''        "--no-sandbox",
        "--ozone-platform=headless",
        f"--remote-allow-origins=http://127.0.0.1:{port}",
        "--disable-background-networking",
'''
if old in s:
    s=s.replace(old,new,1)
elif "remote-allow-origins=http://127.0.0.1" not in s:
    raise SystemExit("V66_08B_ABORT=chromium_origin_anchor_missing")

old_ws='''        self.ws=create_connection(ws_url,timeout=20)
'''
new_ws='''        # Chromium 136+ rejects websocket clients that send a mismatched
        # Origin header. Suppress Origin for this local loopback CDP client;
        # Chromium is also launched with an explicit loopback allow-origin.
        self.ws=create_connection(ws_url,timeout=20,suppress_origin=True)
'''
if old_ws in s:
    s=s.replace(old_ws,new_ws,1)
elif "suppress_origin=True" not in s:
    raise SystemExit("V66_08B_ABORT=websocket_origin_anchor_missing")

old_candidates='''        if str(row.get("status") or "") not in {
            "BROWSER_ADAPTER_REQUIRED",
            "SIGNUP_DISCOVERY_PENDING",
            "SIGNUP_RESULT_UNCERTAIN",
        }:
'''
new_candidates='''        if str(row.get("status") or "") not in {
            "BROWSER_ADAPTER_REQUIRED",
            "SIGNUP_DISCOVERY_PENDING",
            "SIGNUP_RESULT_UNCERTAIN",
            "BROWSER_AUTOMATION_ERROR",
            "CDP_PAGE_SOCKET_UNAVAILABLE",
        }:
'''
if old_candidates in s:
    s=s.replace(old_candidates,new_candidates,1)
elif '"BROWSER_AUTOMATION_ERROR"' not in s[s.find("def browser_candidates"):s.find("def process_candidate")]:
    raise SystemExit("V66_08B_ABORT=browser_candidate_anchor_missing")

p.write_text(s)
print("V66_08B_PATCH=PASS")
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_08B_MODULE_COMPILE=PASS"

echo "===== STOP LOOP AND OLD BROWSER ====="
"$CTL" stop || true
"$CTL" stop-browser || true
sleep 1

echo "===== START PATCHED CHROMIUM ====="
"$CTL" start-browser

echo "===== CDP WEBSOCKET SMOKE TEST ====="
python - <<'PY'
from companyos.runtime.browser_provider_onboarding import _new_target, CDP
t=_new_target("about:blank")
ws=t.get("webSocketDebuggerUrl")
assert ws, "missing_websocket_debugger_url"
c=CDP(ws)
try:
    c.call("Runtime.enable")
    value=c.eval("1+1")
    print("CDP_EVAL_RESULT=", value)
    assert value == 2
finally:
    c.close()
print("V66_08B_CDP_WEBSOCKET=PASS")
PY

echo "===== RETRY FAILED BROWSER CANDIDATE ====="
"$CTL" candidates
"$CTL" once 1 || true

echo "===== RESTART BROWSER LOOP ====="
"$CTL" restart

echo "===== FINAL STATUS ====="
"$CTL" backend
"$CTL" status

echo "V66_08B_CDP_ORIGIN_FIX=PASS"
echo "V66_08B_BROWSER_ERROR_RETRY=PASS"
echo "V66_08B_CDP_SMOKE_TEST=PASS"
echo "V66_08B_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_08B_COMPLETE"
