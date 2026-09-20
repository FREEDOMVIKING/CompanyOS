#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
cd "$ROOT" || exit 1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS PASS 2C STOP CALLER TRACE ====="
echo "MODE=TEMPORARY_INSTRUMENTATION"
echo "NOTE=SOURCE_FILES_ARE_RESTORED_BEFORE_EXIT"
echo "NOTE=NO_EMAIL_SEND"
echo "NOTE=NO_FINANCIAL_ACTION"
echo "NOTE=NO_DEPLOYMENT"
echo

MOD1="companyos/runtime/runtime_control.py"
MOD2="companyos/runtime/service_supervisor.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
B="$RT/audit_repair_backups/stop_trace_$STAMP"
TRACE="$RT/stop_provenance_trace.jsonl"
mkdir -p "$B"
cp "$MOD1" "$B/runtime_control.py"
cp "$MOD2" "$B/service_supervisor.py"
rm -f "$TRACE"

restore() {
  cp "$B/runtime_control.py" "$MOD1" 2>/dev/null || true
  cp "$B/service_supervisor.py" "$MOD2" 2>/dev/null || true
  python -m py_compile "$MOD1" "$MOD2" >/dev/null 2>&1 || true
}
trap restore EXIT INT TERM

echo "===== INSTALL TEMPORARY TRACE HOOKS ====="
python - <<'PY'
from pathlib import Path
import ast

root=Path.home()/"companyos"

p=root/"companyos/runtime/runtime_control.py"
s=p.read_text()
if "COMPANYOS_STOP_PROVENANCE_TRACE" not in s:
    marker="from typing import Any\n"
    helper = r'''
# COMPANYOS_STOP_PROVENANCE_TRACE
def _record_stop_provenance(kind: str) -> None:
    try:
        import traceback
        path = Path.home() / ".companyos_runtime" / "stop_provenance_trace.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": time.time(),
            "kind": kind,
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "argv": list(sys.argv),
            "cwd": os.getcwd(),
            "stack": traceback.format_stack(limit=30),
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        pass
'''
    if marker not in s:
        raise SystemExit("ABORT=runtime_control_import_anchor_missing")
    s=s.replace(marker, marker+helper+"\n", 1)

needle = '    def stop(self, wait_seconds: float = 45.0) -> dict[str, Any]:\n        before = self.status()\n'
replacement = '    def stop(self, wait_seconds: float = 45.0) -> dict[str, Any]:\n        _record_stop_provenance("UnifiedRuntimeControl.stop")\n        before = self.status()\n'
if needle not in s:
    raise SystemExit("ABORT=runtime_control_stop_anchor_missing")
s=s.replace(needle,replacement,1)
ast.parse(s)
p.write_text(s)

p=root/"companyos/runtime/service_supervisor.py"
s=p.read_text()
if "COMPANYOS_REQUEST_STOP_PROVENANCE_TRACE" not in s:
    marker="from typing import Iterable\n"
    helper = r'''
# COMPANYOS_REQUEST_STOP_PROVENANCE_TRACE
def _record_request_stop_provenance(kind: str) -> None:
    try:
        import traceback
        path = Path.home() / ".companyos_runtime" / "stop_provenance_trace.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": time.time(),
            "kind": kind,
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "argv": list(sys.argv),
            "cwd": os.getcwd(),
            "stack": traceback.format_stack(limit=30),
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        pass
'''
    if marker not in s:
        raise SystemExit("ABORT=service_supervisor_import_anchor_missing")
    s=s.replace(marker, marker+helper+"\n", 1)

needle = '    def request_stop(self) -> None:\n        self.stop_path.write_text(f"pid={os.getpid()}\\n", encoding="utf-8")\n'
replacement = '    def request_stop(self) -> None:\n        _record_request_stop_provenance("ServiceSupervisor.request_stop")\n        self.stop_path.write_text(f"pid={os.getpid()}\\n", encoding="utf-8")\n'
if needle not in s:
    raise SystemExit("ABORT=service_supervisor_request_stop_anchor_missing")
s=s.replace(needle,replacement,1)
ast.parse(s)
p.write_text(s)

print("TRACE_HOOKS=PASS")
PY
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "TRACE_ABORT=patch_failed"
  exit "$rc"
fi

python -m py_compile "$MOD1" "$MOD2" || exit $?
echo "TRACE_COMPILE=PASS"

echo
echo "===== ENSURE CLEAN STOPPED BASELINE ====="
scripts/companyosctl stop >/dev/null 2>&1 || true
sleep 2
rm -f "$RT/SUPERVISOR_STOP" || true
rm -f "$TRACE" || true

echo
echo "===== START CANONICAL RUNTIME FOR TRACE WINDOW ====="
export COMPANYOS_ENABLE_SELF_EVOLUTION=0
export COMPANYOS_ENABLE_LIVE_FINANCE=0
export COMPANYOS_ENABLE_EXTERNAL_ACTIONS=0
scripts/companyosctl recover
start_rc=$?
echo "START_RC=$start_rc"
if [ "$start_rc" -ne 0 ]; then
  echo "TRACE_ABORT=start_failed"
  exit "$start_rc"
fi

echo
echo "===== WATCH 30 SECONDS FOR UNEXPECTED STOP ====="
for i in $(seq 1 30); do
  sleep 1
  status="$(python - <<'PY'
from pathlib import Path
from companyos.runtime.runtime_control import UnifiedRuntimeControl
s=UnifiedRuntimeControl(Path.home()/"companyos").status()
print(("1" if s.get("supervisor_alive") else "0")+" "+("1" if s.get("stop_requested") else "0")+" "+str(s.get("supervisor_pid") or 0))
PY
)"
  alive="$(printf '%s' "$status" | awk '{print $1}')"
  stop="$(printf '%s' "$status" | awk '{print $2}')"
  pid="$(printf '%s' "$status" | awk '{print $3}')"
  echo "t=${i}s supervisor_alive=$alive stop_requested=$stop pid=$pid"
  if [ "$alive" = "0" ] || [ "$stop" = "1" ]; then
    echo "UNEXPECTED_STOP_OBSERVED_AT=${i}s"
    break
  fi
done

echo
echo "===== STOP PROVENANCE TRACE ====="
if [ -f "$TRACE" ]; then
  python - "$TRACE" <<'PY'
import json,sys
p=sys.argv[1]
for line in open(p,errors="ignore"):
    try:
        x=json.loads(line)
    except Exception:
        continue
    print("---- STOP EVENT ----")
    print("ts=",x.get("ts"))
    print("kind=",x.get("kind"))
    print("pid=",x.get("pid"),"ppid=",x.get("ppid"))
    print("argv=",x.get("argv"))
    print("cwd=",x.get("cwd"))
    print("stack:")
    for row in x.get("stack") or []:
        print(row.rstrip())
PY
else
  echo "TRACE_FILE=NONE"
fi

echo
echo "===== STOP MARKER ====="
if [ -e "$RT/SUPERVISOR_STOP" ]; then
  echo "SUPERVISOR_STOP_EXISTS=true"
  stat "$RT/SUPERVISOR_STOP" 2>/dev/null || true
  printf 'contents='
  cat "$RT/SUPERVISOR_STOP" 2>/dev/null || true
else
  echo "SUPERVISOR_STOP_EXISTS=false"
fi

echo
echo "===== LAST CONTROL LOG EVENTS ====="
tail -n 80 "$RT/runtime_control.log" 2>/dev/null || true
echo
tail -n 120 "$RT/service_supervisor.log" 2>/dev/null || true

echo
echo "===== CLEANUP RUNTIME ====="
scripts/companyosctl stop >/dev/null 2>&1 || true
sleep 2
rm -f "$RT/SUPERVISOR_STOP" || true

echo
echo "===== RESTORE SOURCE ====="
restore
trap - EXIT INT TERM
echo "SOURCE_RESTORED=PASS"

echo
echo "===== GIT STATUS ====="
git --no-pager status --short

echo
echo "COMPANYOS_PASS_2C_STOP_CALLER_TRACE=COMPLETE"
