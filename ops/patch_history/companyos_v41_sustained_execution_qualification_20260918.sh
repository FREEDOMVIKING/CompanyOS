#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "${HOME}/companyos"
R="${HOME}/.companyos_runtime"
Q="${R}/task_queue"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="${R}/v41_sustained_qualification_${TS}.log"
mkdir -p "$R"

exec > >(tee -a "$OUT") 2>&1
echo "===== COMPANYOS V41 SUSTAINED EXECUTION QUALIFICATION ====="
echo "START=$(date -Is)"
echo "NON_DESTRUCTIVE=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"

count_states () {
python - "$Q" <<'PY'
import json,sys
from pathlib import Path
q=Path(sys.argv[1])
c={}
for f in q.glob("*.json"):
    try:
        d=json.loads(f.read_text())
        s=str(d.get("state","UNKNOWN")).upper()
        c[s]=c.get(s,0)+1
    except Exception:
        c["UNREADABLE"]=c.get("UNREADABLE",0)+1
print(" ".join(f"{k}={v}" for k,v in sorted(c.items())))
PY
}

getn () {
  local key="$1"
  count_states | tr ' ' '\n' | awk -F= -v k="$key" '$1==k{print $2}' | tail -1
}

echo "===== PROCESS SINGLETON CHECK ====="
SUP="$(pgrep -af 'companyos/runtime/service_supervisor.py' | grep -v grep | wc -l || true)"
CONT="$(pgrep -af 'continuous_goal_runtime' | grep -v grep | wc -l || true)"
echo "SUPERVISOR_COUNT=$SUP CONTINUOUS_COUNT=$CONT"
if [ "$SUP" -ne 1 ] || [ "$CONT" -ne 1 ]; then
  echo "V41_ABORT=runtime_singleton_contract_failed"
  exit 23
fi
echo "SINGLETON=PASS"

echo "===== REGRESSION ====="
python -m pytest -q \
 tests/test_v39_dispatch_result_repair.py \
 tests/test_v36_live_recovery_qualification.py \
 tests/test_v34_worker_lease_store.py 2>/dev/null || {
   echo "REGRESSION=FAIL"
   exit 24
}
echo "REGRESSION=PASS"

C0="$(getn COMPLETED || echo 0)"
F0="$(getn FAILED || echo 0)"
Q0="$(getn QUEUED || echo 0)"
echo "T+000 COMPLETED=$C0 FAILED=$F0 QUEUED=$Q0"

# Five minutes: enough to expose stalls without an expensive full diagnostic.
for t in 60 120 180 240 300; do
  sleep 60
  C="$(getn COMPLETED || echo 0)"
  F="$(getn FAILED || echo 0)"
  QQ="$(getn QUEUED || echo 0)"
  echo "T+$(printf '%03d' "$t") COMPLETED=$C FAILED=$F QUEUED=$QQ completed_delta=$((C-C0)) failed_delta=$((F-F0)) queued_delta=$((QQ-Q0))"
done

C1="$(getn COMPLETED || echo 0)"
F1="$(getn FAILED || echo 0)"
Q1="$(getn QUEUED || echo 0)"
DC=$((C1-C0)); DF=$((F1-F0)); DQ=$((Q1-Q0))
echo "FINAL_COMPLETED_DELTA=$DC"
echo "FINAL_FAILED_DELTA=$DF"
echo "FINAL_QUEUED_DELTA=$DQ"

echo "===== FAILURE SIGNATURE SAMPLE ====="
python - "$Q" <<'PY'
import json,sys,collections
from pathlib import Path
q=Path(sys.argv[1]); c=collections.Counter()
for f in q.glob("*.json"):
    try:
        d=json.loads(f.read_text())
        if str(d.get("state","")).upper()=="FAILED":
            e=str(d.get("last_error") or d.get("error") or "").strip()
            if e: c[e[:220]]+=1
    except Exception: pass
for e,n in c.most_common(8):
    print(f"{n}x {e}")
PY

echo "===== RUNTIME RECHECK ====="
SUP2="$(pgrep -af 'companyos/runtime/service_supervisor.py' | grep -v grep | wc -l || true)"
CONT2="$(pgrep -af 'continuous_goal_runtime' | grep -v grep | wc -l || true)"
echo "SUPERVISOR_COUNT=$SUP2 CONTINUOUS_COUNT=$CONT2"

PASS=YES
[ "$SUP2" -eq 1 ] || PASS=NO
[ "$CONT2" -eq 1 ] || PASS=NO
[ "$DC" -gt 0 ] || PASS=NO
# V40 established zero-new-failure behavior; hold that contract.
[ "$DF" -eq 0 ] || PASS=NO

if [ "$PASS" = YES ]; then
 echo "V41_SUSTAINED_EXECUTION=PASS"
else
 echo "V41_SUSTAINED_EXECUTION=NEEDS_DIAGNOSIS"
fi
echo "SUPERVISOR_RESTARTED=NO"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "REPORT=$OUT"
echo "END=$(date -Is)"
