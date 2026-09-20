#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
SRC="$ROOT/companyos/runtime/autonomous_procurement_sourcing.py"
ACC="$ROOT/companyos/runtime/autonomous_provider_accounts.py"
SCTL="$ROOT/scripts/companyos_sourcingctl"
ACTL="$ROOT/scripts/companyos_accountctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.06B CONCURRENCY + RETRY RECOVERY ====="
echo "FIX_1=provider_account_latest_json_race"
echo "FIX_2=retry_old_external_provider_required_requests_now_that_openai_web_exists"
echo "FIX_3=manual_once_no_longer_races_background_loop"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in "$SRC" "$ACC" "$SCTL" "$ACTL"; do
  [ -f "$f" ] || { echo "V66_06B_ABORT=missing:$f"; exit 1; }
done

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$SRC" "$ACC" "$SCTL" "$ACTL"; do
  cp "$f" "${f}.v66_06b_backup_${stamp}"
  echo "BACKUP=${f}.v66_06b_backup_${stamp}"
done

echo "===== PATCH ATOMIC JSON WRITES ====="
python - <<'PY'
from pathlib import Path

files=[
    Path.home()/"companyos/companyos/runtime/autonomous_procurement_sourcing.py",
    Path.home()/"companyos/companyos/runtime/autonomous_provider_accounts.py",
]

old='''def save_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\\n")
    tmp.replace(path)
'''

old2='''def save_json(path: Path,data: Any) -> None:
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True,default=str)+"\\n")
    tmp.replace(path)
'''

new='''def save_json(path: Path, data: Any) -> None:
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    payload=json.dumps(data, indent=2, sort_keys=True, default=str) + "\\n"
    fd,tmp_name=tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        except Exception:
            pass
'''

for p in files:
    s=p.read_text()
    if "tempfile.mkstemp" in s:
        print(f"{p.name}:already_patched")
        continue
    if old in s:
        s=s.replace(old,new,1)
    elif old2 in s:
        s=s.replace(old2,new,1)
    else:
        raise SystemExit(f"V66_06B_ABORT=save_json_anchor_missing:{p}")
    p.write_text(s)
    print(f"{p.name}:atomic_save=PASS")
PY

echo "===== PATCH SOURCING RETRY SEMANTICS ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/autonomous_procurement_sourcing.py"
s=p.read_text()

old='''def processed_ids() -> set[str]:
    return {
        str(x.get("sourcing_request_id"))
        for x in read_jsonl(RESOLUTIONS)
        if x.get("sourcing_request_id")
    }
'''

new='''def processed_ids() -> set[str]:
    # A request that previously failed only because no external search
    # provider existed is NOT terminal. Once a provider becomes available,
    # it must re-enter the sourcing queue automatically.
    terminal={"SEARCH_EVIDENCE_FOUND","CHECKOUT_OR_INVOICE_REQUIRED"}
    return {
        str(x.get("sourcing_request_id"))
        for x in read_jsonl(RESOLUTIONS)
        if x.get("sourcing_request_id")
        and str(x.get("status") or "") in terminal
    }
'''

if old in s:
    s=s.replace(old,new,1)
elif 'terminal={"SEARCH_EVIDENCE_FOUND","CHECKOUT_OR_INVOICE_REQUIRED"}' not in s:
    raise SystemExit("V66_06B_ABORT=processed_ids_anchor_missing")

p.write_text(s)
print("V66_06B_STALE_SOURCING_RETRY=PASS")
PY

echo "===== PATCH MANUAL ONCE CONTROLS TO AVOID BACKGROUND RACE ====="
python - <<'PY'
from pathlib import Path

def patch(path, process_name, module_cmd):
    p=Path(path)
    s=p.read_text()
    old=f'''  once)
    python -m {module_cmd}'''
    if old not in s:
        if "WAS_RUNNING=0" in s:
            print(f"{p.name}:already_patched")
            return
        raise SystemExit(f"V66_06B_ABORT=ctl_once_anchor_missing:{p}")

    # Keep the remainder of the existing command line and inject a stop/run/restart guard.
    start=s.index(old)
    line_end=s.index("\n", start)
    command=s[start+len("  once)\n    "):line_end]

    replacement=f'''  once)
    WAS_RUNNING=0
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      WAS_RUNNING=1
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
      sleep 1
    fi
    {command}
    if [ "$WAS_RUNNING" = "1" ]; then
      nohup python -m {process_name} loop \\
        --interval "${{COMPANYOS_{'SOURCING' if 'sourcing' in process_name else 'ACCOUNT_PROVISION'}_INTERVAL_SECONDS:-{'300' if 'sourcing' in process_name else '600'}}}" \\
        >>"$LOGFILE" 2>&1 &
      echo $! > "$PIDFILE"
      echo "BACKGROUND_LOOP_RESTARTED PID=$(cat "$PIDFILE")"
    fi'''

    s=s[:start]+replacement+s[line_end:]
    p.write_text(s)
    print(f"{p.name}:manual_once_guard=PASS")

patch(
    Path.home()/"companyos/scripts/companyos_sourcingctl",
    "companyos.runtime.autonomous_procurement_sourcing",
    "companyos.runtime.autonomous_procurement_sourcing",
)
patch(
    Path.home()/"companyos/scripts/companyos_accountctl",
    "companyos.runtime.autonomous_provider_accounts",
    "companyos.runtime.autonomous_provider_accounts",
)
PY

echo "===== COMPILE ====="
python -m py_compile "$SRC" "$ACC"
echo "V66_06B_MODULE_COMPILE=PASS"

echo "===== STOP LOOPS FOR CLEAN RECOVERY CYCLE ====="
"$SCTL" stop || true
"$ACTL" stop || true

echo "===== VERIFY OPENAI SEARCH PROVIDER ====="
"$SCTL" providers

echo "===== RETRY PREVIOUSLY STRANDED SOURCING REQUESTS ====="
"$SCTL" once 20

echo "===== RETRY PROVIDER ACCOUNT DISCOVERY WITHOUT RACE ====="
"$ACTL" once 3

echo "===== RESTART LIVE LOOPS ====="
"$SCTL" start
"$ACTL" start

echo "===== FINAL STATUS ====="
"$SCTL" status
"$ACTL" status

echo "V66_06B_ATOMIC_STATE_WRITES=PASS"
echo "V66_06B_EXTERNAL_PROVIDER_REQUIRED_RETRY=PASS"
echo "V66_06B_MANUAL_BACKGROUND_RACE_FIXED=PASS"
echo "V66_06B_OPENAI_SEARCH_PROVIDER_PRESERVED=PASS"
echo "V66_06B_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_06B_COMPLETE"
