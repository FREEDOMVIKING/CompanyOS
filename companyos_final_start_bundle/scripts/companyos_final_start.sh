#!/data/data/com.termux/files/usr/bin/bash
set -u
ROOT="$HOME/companyos"
export PYTHONPATH="$ROOT:$ROOT/companyos"
SERVICE="$ROOT/scripts/companyos_service.sh"
OLD="$ROOT/scripts/companyos_final_launch.sh"
CMD="${1:-status}"

gate() {
python - <<'PY'
import json
from companyos.walletintegration.canonical_startup_gate import verify_startup
print(json.dumps(verify_startup(), indent=2))
PY
}

case "$CMD" in
  preflight) gate; [ -x "$OLD" ] && bash "$OLD" preflight || true ;;
  status) gate; [ -x "$SERVICE" ] && bash "$SERVICE" status || true ;;
  trial-check) gate; [ -x "$OLD" ] && bash "$OLD" trial-check || true; echo NO_TRANSACTION_SENT ;;
  full-check) gate; [ -x "$OLD" ] && bash "$OLD" full-check || true; echo NO_TRANSACTION_SENT ;;
  start)
    python - <<'PY'
from companyos.walletintegration.canonical_startup_gate import require_startup
r=require_startup()
print("STARTUP_GATE: PASS")
print("WALLET:",r["wallet"])
print("PRIVATE_KEY: HIDDEN")
PY
    [ -x "$SERVICE" ] || { echo SERVICE_SCRIPT_MISSING; exit 1; }
    exec bash "$SERVICE" start
    ;;
  stop) exec bash "$SERVICE" stop ;;
  restart) "$0" stop || true; sleep 2; exec "$0" start ;;
  logs) exec bash "$SERVICE" logs ;;
  *) echo "Usage: $0 {preflight|status|trial-check|full-check|start|stop|restart|logs}"; exit 2 ;;
esac
