#!/data/data/com.termux/files/usr/bin/bash
set -u
ROOT="$HOME/companyos"
RUNTIME="$ROOT/.companyos_runtime"
PIDFILE="$RUNTIME/companyos_full_autonomy.pid"
LOGFILE="$RUNTIME/companyos_full_autonomy.log"
POLICY="$RUNTIME/full_autonomy_mode.json"
RUNNER="$ROOT/scripts/companyos_full_autonomy_runner.py"
export PYTHONPATH="$ROOT:$ROOT/companyos"
mkdir -p "$RUNTIME"

running() {
  [ -f "$PIDFILE" ] || return 1
  PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null
}

case "${1:-status}" in
activate)
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/".companyos_runtime"/"full_autonomy_mode.json"
p.write_text(json.dumps({
"mode":"FULL_AUTONOMY",
"continuous_runtime":True,
"autonomous_goal_creation":True,
"research":True,"planning":True,"delegation":True,"building":True,
"evaluation":True,"follow_up_goals":True,"self_improvement":True,
"external_actions_capable":True,"transaction_broadcast_capable":True,
"canonical_signer_required":True,"live_limits_required":True,
"consequential_action_approval_gates_preserved":True,
"reconciliation_required":True
},indent=2)+"\n")
print("FULL_AUTONOMY_MODE: ACTIVATED")
print("SAFETY_GATES_BYPASSED: NO")
PY
;;
start)
python - <<'PY'
from companyos.walletintegration.canonical_startup_gate import verify_startup
r=verify_startup()
print("STARTUP_GATE:", "PASS" if r.get("ready") else "FAIL")
print("WALLET:",r.get("wallet"))
print("RPC_LOADED:",r.get("rpc_loaded"))
print("PRIVATE_KEY_LOADED:",r.get("private_key_loaded"))
print("PRIVATE_KEY_DISPLAYED: False")
if not r.get("ready"): raise SystemExit("START_ABORTED")
PY
[ -f "$POLICY" ] || "$0" activate
if running; then echo "COMPANYOS_FULL_AUTONOMY_ALREADY_RUNNING pid=$(cat "$PIDFILE")"; exit 0; fi
nohup python "$RUNNER" >> "$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
sleep 2
if kill -0 "$PID" 2>/dev/null; then
  echo "COMPANYOS_FULL_AUTONOMY_STARTED pid=$PID"
  tail -n 20 "$LOGFILE" 2>/dev/null || true
else
  echo "COMPANYOS_FULL_AUTONOMY_START_FAILED"
  tail -n 100 "$LOGFILE" 2>/dev/null || true
  rm -f "$PIDFILE"
  exit 1
fi
;;
status)
if running; then echo "COMPANYOS_FULL_AUTONOMY_RUNNING pid=$(cat "$PIDFILE")"; else echo "COMPANYOS_FULL_AUTONOMY_STOPPED"; fi
[ -f "$POLICY" ] && cat "$POLICY" || echo "FULL_AUTONOMY_MODE_NOT_ACTIVATED"
[ -f "$RUNTIME/autonomous_ceo_runtime_service.json" ] && cat "$RUNTIME/autonomous_ceo_runtime_service.json" || true
;;
logs)
touch "$LOGFILE"
tail -n 150 -f "$LOGFILE"
;;
stop)
if running; then PID="$(cat "$PIDFILE")"; kill "$PID" 2>/dev/null || true; sleep 2; fi
rm -f "$PIDFILE"
echo "COMPANYOS_FULL_AUTONOMY_STOPPED"
;;
restart)
"$0" stop
exec "$0" start
;;
*)
echo "Usage: $0 {activate|start|status|logs|stop|restart}"
exit 2
;;
esac
