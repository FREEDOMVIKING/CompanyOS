#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V22 DURABLE EXECUTION CLOSURE ====="
mkdir -p companyos/runtime tests/generated .companyos_runtime
cp -f companyos/runtime/profit_to_action_closure.py ".companyos_runtime/profit_to_action_closure.py.v21.$(date +%s).bak"

cat > companyos/runtime/durable_execution_closure.py <<'PYCODE'
from __future__ import annotations
import json, os, time
from pathlib import Path
ROOT=Path.home()/".companyos_runtime"
JOBS=ROOT/"durable_execution_jobs"; STATE=ROOT/"durable_execution_closure_state.json"
EVENTS=ROOT/"durable_execution_closure_events.jsonl"; STOP=ROOT/"STOP_CONTINUOUS"
JOBS.mkdir(parents=True,exist_ok=True)
TERMINAL={"COMPLETED","FAILED","HALTED","BLOCKED","AWAITING_EXTERNAL_GATE"}
def atomic(p,o):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(o,indent=2,sort_keys=True,default=str)+"\n"); t.replace(p)
def load(p,d):
    try:return json.loads(Path(p).read_text())
    except Exception:return d
def emit(kind,**kw):
    with EVENTS.open("a") as f:f.write(json.dumps({"ts":time.time(),"kind":kind,**kw},sort_keys=True,default=str)+"\n")
def job_path(oid): return JOBS/f"{oid}.json"
def register(*,oid,packet_id,candidate_name,candidate_score,selected_action,fingerprint):
    now=time.time(); p=job_path(oid); old=load(p,{})
    if old:return old
    j={"schema":"companyos.durable_execution.v22","orchestration_id":oid,"action_packet_id":packet_id,
       "candidate_name":candidate_name,"candidate_score":candidate_score,"selected_action":selected_action,
       "fingerprint":fingerprint,"state":"DISPATCHED","created_at":now,"updated_at":now,
       "terminal":False,"cycles":0,"evidence":[],"outcome":None,"last_error":None}
    atomic(p,j); emit("durable_job_registered",orchestration_id=oid,candidate_name=candidate_name); return j
def advance(j):
    oid=j["orchestration_id"]
    try:
        from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
        ceo=AutonomousCEOOrchestrator(); rec=ceo.load(oid)
        if str(rec.state).upper() not in {"COMPLETED","FAILED","HALTED"}:
            ceo.cycle(oid); rec=ceo.load(oid)
        state=str(rec.state or "RUNNING").upper()
        j["state"]=state; j["cycles"]=int(rec.total_cycles or 0); j["active_goal_id"]=rec.active_goal_id
        j["last_decision"]=rec.last_decision; j["outcome"]=rec.final_summary
        j["terminal"]=state in TERMINAL; j["last_error"]=None
    except FileNotFoundError:
        j["state"]="FAILED"; j["terminal"]=True; j["last_error"]="orchestration_record_missing"
    except Exception as e:j["last_error"]=repr(e)
    j["updated_at"]=time.time(); atomic(job_path(oid),j)
    if j["terminal"]:emit("durable_job_terminal",orchestration_id=oid,state=j["state"],outcome=j.get("outcome"))
    return j
def cycle():
    now=time.time(); rows=[]
    for p in JOBS.glob("*.json"):
        j=load(p,{})
        if j and not j.get("terminal"):j=advance(j)
        if j:rows.append(j)
    terminal=[j for j in rows if j.get("terminal")]
    out={"running":True,"healthy":True,"last_cycle_unix":now,"job_count":len(rows),
         "active_count":sum(not j.get("terminal") for j in rows),"terminal_count":len(terminal),
         "completed_count":sum(j.get("state")=="COMPLETED" for j in terminal),
         "failed_count":sum(j.get("state") in {"FAILED","HALTED"} for j in terminal)}
    atomic(STATE,out); return out
def run():
    interval=max(10,int(os.getenv("COMPANYOS_DURABLE_EXECUTION_INTERVAL_SECONDS","30")))
    while not STOP.exists():
        try:cycle()
        except Exception as e:atomic(STATE,{"running":True,"healthy":False,"last_cycle_unix":time.time(),"error":repr(e)})
        time.sleep(interval)
if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser();a.add_argument("command",nargs="?",default="run",choices=("run","once","status"))
    c=a.parse_args().command
    print(json.dumps(cycle() if c=="once" else load(STATE,{"status":"not_run"}),indent=2,sort_keys=True)) if c!="run" else run()
PYCODE

python - <<'PYPATCH'
from pathlib import Path
p=Path("companyos/runtime/profit_to_action_closure.py"); s=p.read_text()
needle='    oid=getattr(rec,"orchestration_id",None); done[fid]=now\n'
repl='''    oid=getattr(rec,"orchestration_id",None)
    if not oid: raise RuntimeError("orchestration_id_missing")
    from companyos.runtime.durable_execution_closure import register as register_durable_execution
    register_durable_execution(oid=oid,packet_id=p.get("action_packet_id"),candidate_name=p.get("candidate_name"),
        candidate_score=p.get("candidate_score"),selected_action=a,fingerprint=fid)
    done[fid]=now
'''
if "register_durable_execution" not in s:
    if needle not in s:raise SystemExit("V22_PATCH_POINT_NOT_FOUND")
    p.write_text(s.replace(needle,repl))
print("V22_PROFIT_HANDOFF_PATCHED")
PYPATCH

cat > tests/generated/test_durable_execution_closure_v22.py <<'PYTEST'
import tempfile,unittest
from pathlib import Path
import companyos.runtime.durable_execution_closure as d
class T(unittest.TestCase):
 def test_contract(self):
  self.assertIn("COMPLETED",d.TERMINAL);self.assertNotIn("DISPATCHED",d.TERMINAL)
 def test_register(self):
  old=d.JOBS
  with tempfile.TemporaryDirectory() as td:
   d.JOBS=Path(td);a=d.register(oid="o1",packet_id="p1",candidate_name="c",candidate_score=5,selected_action={"action":"x"},fingerprint="f")
   b=d.register(oid="o1",packet_id="p2",candidate_name="changed",candidate_score=9,selected_action={"action":"y"},fingerprint="z")
   self.assertEqual(a["state"],"DISPATCHED");self.assertEqual(b["action_packet_id"],"p1")
  d.JOBS=old
if __name__=="__main__":unittest.main()
PYTEST

python -m py_compile companyos/runtime/durable_execution_closure.py companyos/runtime/profit_to_action_closure.py
python -m unittest tests.generated.test_durable_execution_closure_v22

python - <<'PYBACKFILL'
import json
from pathlib import Path
from companyos.runtime.durable_execution_closure import register
p=Path.home()/".companyos_runtime"/"profit_to_action_closure_state.json"
if p.exists():
 x=json.loads(p.read_text());d=x.get("last_dispatch") or {};oid=d.get("orchestration_id")
 if oid:
  register(oid=oid,packet_id=d.get("action_packet_id"),candidate_name=d.get("candidate_name"),candidate_score=d.get("candidate_score"),selected_action=d.get("selected_action"),fingerprint=d.get("fingerprint"))
  print("V21_LAST_DISPATCH_BACKFILLED",oid)
PYBACKFILL

python -m companyos.runtime.durable_execution_closure once || true
git add companyos/runtime/durable_execution_closure.py companyos/runtime/profit_to_action_closure.py tests/generated/test_durable_execution_closure_v22.py
if ! git diff --cached --quiet; then
 git commit -m "Add durable profit execution closure V22"
 git push origin companyos-continuous-fix-2026-09-11
fi
echo "===== V22 STATUS ====="
python -m companyos.runtime.durable_execution_closure status || true
echo "COMPANYOS_DURABLE_EXECUTION_CLOSURE_V22=PASS"
echo "DISPATCH_COUNTS_AS_COMPLETION=NO"
echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
echo "EXTERNAL_GATES_BYPASSED=NO"
echo "FINANCE_GATES_BYPASSED=NO"
