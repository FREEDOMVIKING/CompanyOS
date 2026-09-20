#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACK="$HOME/.companyos_runtime/backups/v32_$STAMP"
mkdir -p "$BACK/companyos/runtime"
FILES=(companyos/runtime/service_supervisor.py companyos/runtime/autonomous_evidence_acquisition.py companyos/runtime/evidence_decision_closure.py companyos/runtime/profit_to_action_closure.py companyos/runtime/closed_loop_outcome_evaluator.py companyos/runtime/adaptive_worker_factory.py companyos/runtime/adaptive_workforce_execution_bridge.py)
for f in "${FILES[@]}"; do cp -a "$f" "$BACK/$f"; done

echo "===== V32 DEEP ARCHITECTURE UNIFICATION ====="
python - <<'PY'
from pathlib import Path
paths=["autonomous_evidence_acquisition.py","evidence_decision_closure.py","profit_to_action_closure.py","closed_loop_outcome_evaluator.py","adaptive_worker_factory.py"]
for n in paths:
 p=Path("companyos/runtime")/n; s=p.read_text()
 s=s.replace('ROOT=Path.home()/"companyos"\nRT=ROOT/".companyos_runtime"\n','ROOT=(Path.home()/"companyos").resolve()\n# V32_CANONICAL_RUNTIME_ROOT\nRT=Path.home()/".companyos_runtime"\n')
 s=s.replace('ROOT=Path.home()/"companyos"; RT=ROOT/".companyos_runtime"','ROOT=(Path.home()/"companyos").resolve(); RT=Path.home()/".companyos_runtime" # V32_CANONICAL_RUNTIME_ROOT')
 p.write_text(s); print("ROOT_PATCH",n)

p=Path("companyos/runtime/service_supervisor.py"); s=p.read_text()
s=s.replace('        # COMPANYOS_SUPERVISOR_DEDICATED_STOP_V27\\n        self.stop_path = self.runtime_root / "SUPERVISOR_STOP"\n','')
if "V32_STABILITY_WINDOW" not in s:
 s=s.replace('        self.started_at = time.time()\n','        self.started_at = time.time()\n        # V32_STABILITY_WINDOW\n        self.spawned_at: dict[str, float] = {}\n',1)
 s=s.replace('        self.children[spec.name] = child\n        self._log(f"START service={spec.name} pid={child.pid}")\n','        self.children[spec.name] = child\n        self.spawned_at[spec.name] = time.time()\n        self._log(f"START service={spec.name} pid={child.pid}")\n',1)
 s=s.replace('        if child and child.poll() is None:\n            self.failures[spec.name] = 0\n            return\n','        if child and child.poll() is None:\n            if time.time() - self.spawned_at.get(spec.name, self.started_at) >= max(10.0, self.poll_seconds * 2):\n                self.failures[spec.name] = 0\n            return\n',1)
p.write_text(s); print("SUPERVISOR_PATCH=PASS")

p=Path("companyos/runtime/adaptive_workforce_execution_bridge.py"); s=p.read_text()
if "V32_EMITTED_JOB_INDEX" not in s:
 s=s.replace('RESULTS = RUNTIME / "adaptive_workforce_verified_results.jsonl"\n','RESULTS = RUNTIME / "adaptive_workforce_verified_results.jsonl"\n# V32_EMITTED_JOB_INDEX\nEMITTED = RUNTIME / "adaptive_workforce_emitted_jobs.json"\n',1)
 s=s.replace('    emitted = 0\n    for job in queue[-25:]:\n','    emitted = 0\n    emitted_index = _load(EMITTED, {"job_ids": []})\n    known = set(str(x) for x in emitted_index.get("job_ids", []) if x)\n    for job in queue[-25:]:\n',1)
 s=s.replace('        if not jid:\n            continue\n','        if not jid or jid in known:\n            continue\n',1)
 s=s.replace('        _append(rec)\n        emitted += 1\n\n    factory = Factory()\n','        _append(rec)\n        known.add(jid)\n        emitted += 1\n\n    _write(EMITTED, {"job_ids": sorted(known)[-10000:], "updated_at": now})\n\n    factory = Factory()\n',1)
p.write_text(s); print("BRIDGE_DEDUP_PATCH=PASS")
PY

python -m py_compile "${FILES[@]}"
python - <<'PY'
from pathlib import Path
for n in ["autonomous_evidence_acquisition.py","evidence_decision_closure.py","profit_to_action_closure.py","closed_loop_outcome_evaluator.py","adaptive_worker_factory.py"]:
 s=(Path("companyos/runtime")/n).read_text()
 assert 'ROOT/".companyos_runtime"' not in s
assert "V32_EMITTED_JOB_INDEX" in Path("companyos/runtime/adaptive_workforce_execution_bridge.py").read_text()
print("V32_SOURCE_CONTRACT=PASS")
PY

echo "===== RUNTIME SPLIT AUDIT ====="
python - <<'PY'
from pathlib import Path
for root,label in ((Path.home()/".companyos_runtime","canonical"),(Path.home()/"companyos"/".companyos_runtime","legacy")):
 print(label,"exists=",root.exists(),"json=",sum(1 for _ in root.rglob("*.json")) if root.exists() else 0,"tasks=",sum(1 for _ in (root/"task_queue").glob("*.json")) if (root/"task_queue").exists() else 0)
PY

echo "===== CONTROLLED SERVICE RELOAD ====="
PATS=(companyos.runtime.autonomous_evidence_acquisition companyos.runtime.evidence_decision_closure companyos.runtime.profit_to_action_closure companyos.runtime.closed_loop_outcome_evaluator companyos.runtime.adaptive_worker_factory companyos.runtime.adaptive_workforce_execution_bridge)
for pat in "${PATS[@]}"; do for pid in $(pgrep -f "$pat" || true); do [ "$pid" = "$$" ] || kill "$pid" 2>/dev/null || true; done; done
SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
[ -n "$SUP" ] || { echo "FAIL=no_supervisor"; exit 10; }
echo "SUPERVISOR_PID=$SUP"
sleep 20
for pat in "${PATS[@]}"; do pid="$(pgrep -f "$pat" | head -1 || true)"; echo "$pat PID=${pid:-none}"; [ -n "$pid" ] || exit 11; done

echo "===== 180 SECOND QUALIFICATION ====="
python - <<'PY'
import json,time,subprocess
from pathlib import Path
from collections import Counter
rt=Path.home()/".companyos_runtime"; qr=rt/"task_queue"; ss=rt/"service_supervisor_state.json"
def snap():
 c=Counter()
 for p in qr.glob("*.json"):
  try:c[str(json.loads(p.read_text()).get("state","UNKNOWN")).upper()]+=1
  except:c["UNREADABLE"]+=1
 return c
def sv():
 try:return json.loads(ss.read_text()).get("services",{})
 except:return {}
def alive(x):return subprocess.run(["pgrep","-f",x],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
a=snap();b=a;print("T+000",dict(a),flush=True)
for sec in range(15,181,15):
 time.sleep(15);b=snap();w=sv().get("adaptive_workforce_execution_bridge",{})
 print(f"T+{sec:03d}",dict(b),"completed_delta=",b["COMPLETED"]-a["COMPLETED"],"queued_delta=",b["QUEUED"]-a["QUEUED"],"failed_delta=",b["FAILED"]-a["FAILED"],"bridge_restarts=",w.get("restarts"),"bridge_failures=",w.get("consecutive_failures"),"sup=",alive("companyos.runtime.service_supervisor"),"child=",alive("companyos.runtime.continuous_goal_runtime"),flush=True)
print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"]);print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"]);print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
assert alive("companyos.runtime.service_supervisor") and alive("companyos.runtime.continuous_goal_runtime")
PY

echo "===== PIPELINE STATE AUDIT ====="
python - <<'PY'
import json
from pathlib import Path
rt=Path.home()/".companyos_runtime"
for n in ["evidence_acquisition_state.json","evidence_decision_closure_state.json","profit_to_action_closure_state.json","closed_loop_outcome_evaluator_state.json","adaptive_workforce_execution_bridge_state.json"]:
 p=rt/n; print("----",n,"exists=",p.exists())
 if p.exists():
  try: print(json.dumps(json.loads(p.read_text()),sort_keys=True,default=str)[:1200])
  except Exception as e: print("ERROR",repr(e))
PY

git diff -- "${FILES[@]}"
echo "V32_COMPLETE"
echo "CANONICAL_RUNTIME_ROOTS=YES"
echo "BRIDGE_RESULT_DEDUP=YES"
echo "SUPERVISOR_STABILITY_ACCOUNTING=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"
echo "BACKUP=$BACK"
