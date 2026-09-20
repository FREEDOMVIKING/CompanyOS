#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS CONTINUOUS AUTONOMOUS WORKFORCE LOOP V2 ====="
echo "Uses actual Factory.active(worker) contract. No finance mutation. No supervisor restart."

mkdir -p companyos/runtime scripts tests/generated .companyos_runtime/autonomous_workforce

cat > companyos/runtime/autonomous_workforce_loop.py <<'PY'
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
STATE=RT/"autonomous_workforce"
STATE.mkdir(parents=True,exist_ok=True)

from companyos.runtime.adaptive_worker_factory import Factory

def _write(name:str,obj:Any):
    p=STATE/name
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n")
    tmp.replace(p)

def _workers(factory:Factory):
    # Factory.active(t) is a predicate. The canonical worker collection is reg["workers"].
    reg=getattr(factory,"reg",{}) or {}
    ws=reg.get("workers",[])
    return ws if isinstance(ws,list) else []

def _active(factory:Factory):
    out=[]
    for w in _workers(factory):
        try:
            if factory.active(w):
                out.append(w)
        except Exception:
            continue
    return out

def cycle():
    f=Factory()
    before=_active(f)
    result=f.cycle()
    after=_active(f)

    summary={
      "timestamp":time.time(),
      "factory_contract":"reg.workers + active(worker)",
      "workers_total":len(_workers(f)),
      "active_before":len(before),
      "active_after":len(after),
      "permanent":sum(1 for w in _workers(f) if w.get("status")=="permanent"),
      "probation":sum(1 for w in _workers(f) if w.get("status")=="probation"),
      "factory_cycle":result,
      "financial_metrics_invented":False,
    }
    _write("latest.json",summary)
    return summary

def run(interval:int=300):
    while True:
        try:
            cycle()
        except Exception as e:
            _write("error.json",{"timestamp":time.time(),"type":type(e).__name__,"error":str(e)})
        time.sleep(max(60,int(interval)))

if __name__=="__main__":
    print(json.dumps(cycle(),indent=2,default=str))
PY

cat > scripts/companyos_workforce_loop <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import argparse,json
from companyos.runtime.autonomous_workforce_loop import cycle,run
p=argparse.ArgumentParser()
p.add_argument("command",choices=["cycle","run"])
p.add_argument("--interval",type=int,default=300)
a=p.parse_args()
if a.command=="cycle": print(json.dumps(cycle(),indent=2,default=str))
else: run(a.interval)
PY
chmod +x scripts/companyos_workforce_loop

cat > tests/generated/test_autonomous_workforce_loop_v2.py <<'PY'
from companyos.runtime import autonomous_workforce_loop as m

class F:
    def __init__(self):
        self.reg={"workers":[
          {"status":"probation","id":"a"},
          {"status":"permanent","id":"b"},
          {"status":"retired","id":"c"}]}
    def active(self,t):
        return t.get("status") in ("probation","permanent")

def test_actual_factory_contract():
    f=F()
    assert len(m._workers(f))==3
    assert [x["id"] for x in m._active(f)]==["a","b"]

def test_active_is_called_with_worker():
    class X(F):
        def active(self,t):
            assert isinstance(t,dict)
            return super().active(t)
    assert len(m._active(X()))==2

def test_finance_not_implemented_here():
    src=(m.ROOT/"companyos/runtime/autonomous_workforce_loop.py").read_text()
    assert "SOLANA_PRIVATE_KEY" not in src
    assert "finance_ledger" not in src
PY

echo "===== COMPILE + TEST ====="
python -m py_compile companyos/runtime/autonomous_workforce_loop.py
python -m pytest -q tests/generated/test_autonomous_workforce_loop_v2.py

echo "===== LIVE CONTROLLED CYCLE ====="
python scripts/companyos_workforce_loop cycle

echo "===== SUPERVISOR CHECK ====="
python - <<'PY'
import json
from pathlib import Path
p=Path(".companyos_runtime/service_supervisor_state.json")
if not p.exists(): p=Path(".companyos_runtime/service_supervisor/state.json")
if p.exists():
    try:
        d=json.loads(p.read_text())
        print("supervisor_pid:",d.get("supervisor_pid"))
        print("running:",d.get("running"))
        print("stop_requested:",d.get("stop_requested"))
    except Exception as e: print("supervisor state unreadable:",e)
else: print("supervisor state path not found; supervisor was NOT modified")
PY

echo "===== COMMIT ONLY THIS FIX ====="
git add companyos/runtime/autonomous_workforce_loop.py scripts/companyos_workforce_loop tests/generated/test_autonomous_workforce_loop_v2.py
if ! git diff --cached --quiet; then
  git commit -m "fix autonomous workforce loop Factory active worker contract" || true
fi

echo "FACTORY_ACTIVE_CONTRACT=reg.workers_plus_active_worker"
echo "FINANCE_LIMITS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"
echo "COMPANYOS_AUTONOMOUS_WORKFORCE_LOOP_V2=PASS"
