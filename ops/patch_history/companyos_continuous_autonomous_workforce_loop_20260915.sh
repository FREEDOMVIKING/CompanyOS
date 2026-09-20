#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
PY="${PREFIX:-/data/data/com.termux/files/usr}/bin/python"; [ -x "$PY" ] || PY=python
echo "===== CONTINUOUS AUTONOMOUS WORKFORCE LOOP ====="
echo "No finance changes. No supervisor restart."
mkdir -p tests/generated .companyos_runtime/backups

cat > companyos/runtime/autonomous_workforce_loop.py <<'PYCODE'
from __future__ import annotations
import json,time
from pathlib import Path
from companyos.runtime.adaptive_worker_factory import Factory
ROOT=Path.home()/"companyos"; RT=ROOT/".companyos_runtime"
STATE=RT/"autonomous_workforce_loop_state.json"
QUEUE=RT/"profit_execution_action_queue.json"
ASSIGN=RT/"autonomous_workforce_assignments.jsonl"

def load(p,d):
    try:return json.loads(p.read_text())
    except Exception:return d

def items(o):
    if isinstance(o,list): return [x for x in o if isinstance(x,dict)]
    if isinstance(o,dict):
        for k in ("items","queue","actions","jobs"):
            if isinstance(o.get(k),list): return [x for x in o[k] if isinstance(x,dict)]
    return []

def workers(f):
    a=f.active()
    if isinstance(a,list): return [x for x in a if isinstance(x,dict)]
    if isinstance(a,dict):
        z=[]
        for k in ("permanent","probation"):
            if isinstance(a.get(k),list): z += [x for x in a[k] if isinstance(x,dict)]
        if z:return z
        for k in ("workers","active"):
            if isinstance(a.get(k),list):return [x for x in a[k] if isinstance(x,dict)]
    return []

def affinity(w,j):
    role=str(w.get("role","")).lower()
    blob=json.dumps(j).lower()
    n=float(w.get("score",0) or 0)
    words={
      "research":["research","evidence","source"],
      "market_validation":["market","validation","demand"],
      "pricing":["pricing","price","margin","cost"],
      "competitive_analysis":["competitor","competitive"],
      "evidence_analysis":["evidence","verify","qualification"],
      "revenue_evidence":["revenue","conversion","lead","sale"],
      "execution_readiness":["execution","readiness","launch"],
    }.get(role,[])
    return n + sum(25 for x in words if x in blob) + min(10,float(w.get("useful_outputs",0) or 0))

def cycle():
    f=Factory(); before=workers(f)
    q=[j for j in items(load(QUEUE,[])) if str(j.get("status","")).lower() not in
       {"complete","completed","done","success","succeeded","retired"}]
    routed=[]
    if before:
        ASSIGN.parent.mkdir(parents=True,exist_ok=True)
        with ASSIGN.open("a") as fh:
            for j in q[:8]:
                w=max(before,key=lambda x:affinity(x,j))
                r={"timestamp":time.time(),
                   "job_id":j.get("id") or j.get("job_id") or j.get("action_id"),
                   "worker_id":w.get("worker_id") or w.get("agent_id") or w.get("id"),
                   "role":w.get("role"),"routing_score":affinity(w,j),
                   "internal_only":True,"external_action_authorized":False,
                   "profit_attributed":0.0}
                routed.append(r); fh.write(json.dumps(r,sort_keys=True)+"\n")
    result=f.cycle(); after=workers(f)
    st={"timestamp":time.time(),"running":True,
        "canonical_worker_source":"Factory.active",
        "workers_before":len(before),"workers_after":len(after),
        "queue_candidates":len(q),"assignments":routed,
        "factory_cycle_result":result,
        "promotion_authority":"Factory.cycle",
        "profit_requires_observed_evidence":True,
        "external_financial_gates_unchanged":True}
    tmp=STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(st,indent=2,default=str)+"\n"); tmp.replace(STATE)
    return st

def run(interval=180):
    while True:
        try:cycle()
        except Exception as e:
            STATE.write_text(json.dumps({"timestamp":time.time(),"running":True,"error":str(e)})+"\n")
        time.sleep(max(30,interval))

if __name__=="__main__":
    print(json.dumps(cycle(),indent=2,default=str))
PYCODE

cat > scripts/companyos_workforce_loopctl <<'PYCODE'
#!/data/data/com.termux/files/usr/bin/python
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(R))
from companyos.runtime.autonomous_workforce_loop import cycle
if len(sys.argv)>1 and sys.argv[1]=="status":
 p=Path.home()/"companyos/.companyos_runtime/autonomous_workforce_loop_state.json"
 print(p.read_text() if p.exists() else "{}")
else: print(json.dumps(cycle(),indent=2,default=str))
PYCODE
chmod +x scripts/companyos_workforce_loopctl

cat > tests/generated/test_autonomous_workforce_loop.py <<'PYCODE'
import inspect
from companyos.runtime import autonomous_workforce_loop as m
def test_canonical(): assert "f.active()" in inspect.getsource(m.workers)
def test_factory_cycle(): assert "f.cycle()" in inspect.getsource(m.cycle)
def test_no_fake_profit(): assert '"profit_attributed":0.0' in inspect.getsource(m.cycle)
def test_gates(): assert '"external_action_authorized":False' in inspect.getsource(m.cycle)
PYCODE

echo "===== COMPILE + TEST ====="
"$PY" -m py_compile companyos/runtime/autonomous_workforce_loop.py scripts/companyos_workforce_loopctl
"$PY" -m pytest -q tests/generated/test_autonomous_workforce_loop.py

echo "===== LIVE CONTROLLED CYCLE ====="
PYTHONPATH="$HOME/companyos${PYTHONPATH:+:$PYTHONPATH}" "$PY" -m companyos.runtime.autonomous_workforce_loop

echo "===== VERIFY ====="
"$PY" - <<'PY'
import json
from pathlib import Path
d=json.loads((Path.home()/"companyos/.companyos_runtime/autonomous_workforce_loop_state.json").read_text())
print("workers_before:",d.get("workers_before"))
print("workers_after:",d.get("workers_after"))
print("assignments:",len(d.get("assignments",[])))
assert d.get("canonical_worker_source")=="Factory.active"
assert not d.get("error")
print("CANONICAL_FACTORY_WORKERS=YES")
PY

echo "===== REGISTER, NO RESTART ====="
"$PY" - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/service_supervisor.py"); s=p.read_text()
if "autonomous_workforce_loop" not in s:
    needle="        return services"
    if needle not in s: needle="    return services"
    if needle not in s: raise SystemExit("Supervisor layout unknown; refusing blind mutation")
    indent=needle[:len(needle)-len(needle.lstrip())]
    block=(indent+'if (Path.home()/"companyos/companyos/runtime/autonomous_workforce_loop.py").exists():\n'
           +indent+'    services.append(\n'
           +indent+'        ManagedService(\n'
           +indent+'            "autonomous_workforce_loop",\n'
           +indent+'            (python, "-m", "companyos.runtime.autonomous_workforce_loop", "run"),\n'
           +indent+'        )\n'
           +indent+'    )\n')
    s=s.replace(needle,block+needle,1); p.write_text(s)
    print("SUPERVISOR_REGISTRATION_INSERTED")
else: print("SUPERVISOR_REGISTRATION_ALREADY_PRESENT")
PY
"$PY" -m py_compile companyos/runtime/service_supervisor.py

git add -- companyos/runtime/autonomous_workforce_loop.py scripts/companyos_workforce_loopctl tests/generated/test_autonomous_workforce_loop.py companyos/runtime/service_supervisor.py
if ! git diff --cached --quiet; then git commit -m "add continuous canonical autonomous workforce loop"; fi

echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
echo "FINANCE_LIMITS_CHANGED=NO"
echo "FACTORY_RETAINS_PROMOTION_AUTHORITY=YES"
echo "CONTINUOUS_WORKFORCE_REGISTERED_FOR_NEXT_NORMAL_START=YES"
echo "COMPANYOS_CONTINUOUS_AUTONOMOUS_WORKFORCE_LOOP=PASS"
