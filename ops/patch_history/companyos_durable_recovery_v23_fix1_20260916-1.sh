#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V23 FIX1 ====="

python -c '
from pathlib import Path
p=Path("companyos/runtime/durable_execution_closure.py")
s=p.read_text()
if "def recover_existing():" not in s:
    marker="def cycle():"
    if marker not in s: raise SystemExit("CYCLE_MARKER_MISSING")
    fn="""def recover_existing():
    recovered=[]
    orch_root=ROOT / "ceo_orchestrations"
    if not orch_root.exists():
        return recovered
    known={p.stem for p in JOBS.glob("*.json")}
    for op in sorted(orch_root.glob("*.json"), key=lambda x:x.stat().st_mtime):
        try:
            x=json.loads(op.read_text())
            oid=str(x.get("orchestration_id") or op.stem)
            if not oid or oid in known:
                continue
            state=str(x.get("state") or "RUNNING").upper()
            j={"schema":"companyos.durable_execution.v23","orchestration_id":oid,
               "action_packet_id":None,"candidate_name":x.get("root_goal") or oid,
               "candidate_score":None,"selected_action":{"action":x.get("root_goal")},
               "fingerprint":"recovered:"+oid,"state":state,
               "created_at":float(x.get("created_at_unix") or op.stat().st_mtime),
               "updated_at":time.time(),"terminal":state in TERMINAL,
               "cycles":int(x.get("total_cycles") or 0),"evidence":[],
               "outcome":x.get("final_summary"),"last_error":None,"recovered":True}
            atomic(job_path(oid),j); recovered.append(oid); known.add(oid)
            emit("durable_job_recovered",orchestration_id=oid,state=state)
        except Exception as e:
            emit("durable_recovery_error",path=str(op),error=repr(e))
    return recovered

"""
    s=s.replace(marker,fn+marker)
if "recovered=recover_existing()" not in s:
    s=s.replace("def cycle():\n    now=time.time(); rows=[]","def cycle():\n    recovered=recover_existing()\n    now=time.time(); rows=[]")
if "\"recovered_this_cycle\"" not in s:
    s=s.replace("\"failed_count\":sum(j.get(\"state\") in {\"FAILED\",\"HALTED\"} for j in terminal)}",
                "\"failed_count\":sum(j.get(\"state\") in {\"FAILED\",\"HALTED\"} for j in terminal),\"recovered_this_cycle\":len(recovered)}")
p.write_text(s)
print("RECOVERY_CODE_INSTALLED")
'

python -m py_compile companyos/runtime/durable_execution_closure.py
python -m companyos.runtime.durable_execution_closure once

if ! pgrep -f "companyos.runtime.durable_execution_closure run" >/dev/null 2>&1; then
  nohup python -u -m companyos.runtime.durable_execution_closure run > .companyos_runtime/durable_execution_closure_console.log 2>&1 &
  echo $! > .companyos_runtime/durable_execution_closure.pid
fi

sleep 2
python -m companyos.runtime.durable_execution_closure status

git add companyos/runtime/durable_execution_closure.py
if ! git diff --cached --quiet; then
  git commit -m "Fix durable orchestration recovery V23"
  git push origin companyos-continuous-fix-2026-09-11
fi

echo "COMPANYOS_DURABLE_RECOVERY_V23_FIX1=PASS"
echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
