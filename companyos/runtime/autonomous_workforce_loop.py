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
    # Worker registry status is canonical. Factory.active(t) accepts a
    # bottleneck token in this deployed Factory, not a worker dictionary.
    return [w for w in _workers(factory)
            if isinstance(w, dict) and w.get("status") in ("probation", "permanent")]



def workers(factory=None):
    """Backward-compatible public view of active workforce workers.

    Compatibility contract: f.active()
    """
    f = factory if factory is not None else Factory()
    return _workers(f)


def cycle():
    f=Factory()
    before=active(f)
    result=f.cycle()
    after=active(f)

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
        "profit_attributed":0.0,
        "external_action_authorized":False,
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
