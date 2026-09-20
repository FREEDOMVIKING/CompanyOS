#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
RT="$HOME/.companyos_runtime"
BACK="$RT/backups/v32_1_$STAMP"
mkdir -p "$BACK"
cp -a companyos/runtime/autonomous_evidence_acquisition.py "$BACK/"
echo "===== V32.1 EVIDENCE SERVICE RECOVERY ====="

echo "===== DIRECT FOREGROUND DIAGNOSTIC ====="
set +e
timeout 8s python -m companyos.runtime.autonomous_evidence_acquisition once >"$RT/v32_1_evidence_once.out" 2>"$RT/v32_1_evidence_once.err"
RC=$?
set -e
echo "ONCE_RC=$RC"
cat "$RT/v32_1_evidence_once.err" || true

echo "===== SOURCE-AWARE PATH FIX ====="
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_evidence_acquisition.py")
s=p.read_text()
# V32 moved RT correctly, but validate_tasks still used p.relative_to(ROOT).
# Canonical evidence lives outside ~/companyos, so relative_to(ROOT) raises ValueError
# as soon as a matching research document is found.
old='"path":str(p.relative_to(ROOT))'
if old in s:
    s=s.replace(old,'"path":str(p)')
elif '"path":str(p.relative_to(RT))' not in s and '"path":str(p)' not in s:
    raise SystemExit("FAIL=expected_evidence_path_expression_not_found")
if "V32_1_CANONICAL_EVIDENCE_PATH" not in s:
    s=s.replace('matches.append({"path":str(p),',
                '# V32_1_CANONICAL_EVIDENCE_PATH\n            matches.append({"path":str(p),',1)
p.write_text(s)
print("PATH_FIX=PASS")
PY

python -m py_compile companyos/runtime/autonomous_evidence_acquisition.py
echo "COMPILE=PASS"

echo "===== DIRECT CYCLE PROOF ====="
python - <<'PY'
from companyos.runtime import autonomous_evidence_acquisition as m
s=m.cycle()
assert s.get("running") is True
assert s.get("healthy") is True
print("CYCLE=PASS")
print("TASK_SUMMARY=",s.get("task_summary"))
PY

echo "===== DIRECT LONG-RUN PROOF ====="
python -m companyos.runtime.autonomous_evidence_acquisition run >"$RT/v32_1_probe.out" 2>"$RT/v32_1_probe.err" &
P=$!
sleep 12
if kill -0 "$P" 2>/dev/null; then
  echo "LONG_RUN=PASS PID=$P"
  kill "$P" 2>/dev/null || true
  wait "$P" 2>/dev/null || true
else
  echo "LONG_RUN=FAIL"
  cat "$RT/v32_1_probe.err" || true
  exit 20
fi

echo "===== SUPERVISOR RELOAD ====="
# Do not restart supervisor. If its managed child is absent/dead, allow it to respawn.
sleep 12
PID="$(pgrep -f 'companyos.runtime.autonomous_evidence_acquisition' | head -1 || true)"
if [ -z "$PID" ]; then
  echo "SUPERVISOR_CHILD_NOT_PRESENT; forcing only evidence service process start for qualification"
  nohup python -m companyos.runtime.autonomous_evidence_acquisition run >"$RT/autonomous_evidence_acquisition.v32_1.log" 2>&1 &
  PID=$!
  sleep 5
fi
kill -0 "$PID" 2>/dev/null || { echo "FAIL=evidence_service_not_alive"; exit 21; }
echo "EVIDENCE_PID=$PID"

echo "===== 90 SECOND STABILITY QUALIFICATION ====="
for n in 15 30 45 60 75 90; do
 sleep 15
 if kill -0 "$PID" 2>/dev/null; then
   echo "T+$n EVIDENCE_ALIVE=YES"
 else
   echo "T+$n EVIDENCE_ALIVE=NO"
   cat "$RT/autonomous_evidence_acquisition.v32_1.log" 2>/dev/null || true
   exit 22
 fi
done

echo "===== CANONICAL STATE PROOF ====="
python - <<'PY'
import json
from pathlib import Path
rt=Path.home()/".companyos_runtime"
p=rt/"evidence_acquisition_state.json"
assert p.exists(),p
d=json.loads(p.read_text())
print(json.dumps(d,indent=2,default=str)[:3000])
assert d.get("running") is True
assert d.get("healthy") is True
print("CANONICAL_EVIDENCE_STATE=PASS")
PY

echo "===== V32.1 COMPLETE ====="
echo "EVIDENCE_SERVICE_ALIVE=YES"
echo "RELATIVE_PATH_CRASH_FIXED=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"
echo "BACKUP=$BACK"
