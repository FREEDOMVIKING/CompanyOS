from __future__ import annotations
import json,hashlib,time
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve()
RT=Path.home()/".companyos_runtime"  # V32_CANONICAL_RUNTIME_ROOT
STATE=RT/"adaptive_workers"
STATE.mkdir(parents=True,exist_ok=True)
BOTTLENECKS=("execution_readiness","revenue_evidence","market_evidence","pricing","research")
ROLES={"execution_readiness":"execution_readiness","revenue_evidence":"revenue_evidence",
"market_evidence":"market_validation","pricing":"pricing","research":"research"}

def read(p,d):
    try:return json.loads(p.read_text())
    except Exception:return d
def write(p,v):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n"); t.replace(p)


# Legacy/public compatibility exports.
ROLE_ACTIONS = {
    "execution_readiness": "execution_readiness",
    "revenue_evidence": "revenue_evidence",
    "market_validation": "market_validation",
    "pricing": "pricing",
    "research": "research",
}

BUILD_CHECKS = (
    "execution_readiness",
    "revenue_evidence",
    "market_validation",
    "pricing",
    "research",
)

class Factory:
    def __init__(self):
        self.regp=STATE/"registry.json"; self.reg=read(self.regp,{"version":1,"workers":[]})
    def signals(self):
        text=""
        for p in (RT/"profit_execution_action_queue.json",RT/"market_evidence_summary.json",
                  RT/"post_launch_next_action.json",RT/"continuous_profit_improvement/latest.json"):
            try:text+="\n"+p.read_text(errors="ignore")
            except Exception:pass
        x=[b for b in BOTTLENECKS if b in text]
        return x or list(BOTTLENECKS)
    def active(self,b):
        return any(w.get("bottleneck")==b and w.get("status") in ("probation","permanent") for w in self.reg["workers"])
    def spawn(self,b):
        now=time.time(); role=ROLES[b]
        wid=f"{role}-{hashlib.sha256(f'{role}:{b}:{int(now//3600)}'.encode()).hexdigest()[:10]}"
        w={"worker_id":wid,"role":role,"bottleneck":b,"status":"probation","jobs":0,"successes":0,
           "failures":0,"useful_outputs":0,"attributed_profit":0.0,"verified_score":0.0,
           "created_at":now,"updated_at":now}
        self.reg["workers"].append(w); return w
    def metrics(self,w):
        hits=useful=succ=fail=0
        for p in (RT/"ceo_workforce/latest.json",RT/"profit_execution_action_queue.json",
                  RT/"market_evidence_summary.json",RT/"post_launch_next_action.json",
                  RT/"revenue_performance_feedback.json"):
            obj=read(p,None)
            if obj is None:continue
            s=json.dumps(obj).lower()
            if w["worker_id"].lower() in s or w["role"].lower() in s:
                hits+=1
                if '"observed": true' in s or '"verified": true' in s: useful+=1
                if '"success": true' in s: succ+=1
                if '"success": false' in s: fail+=1
        jobs=max(w.get("jobs",0),hits)
        score=min(100.0,useful*20+succ*15+min(jobs,10)*2)
        return jobs,succ,fail,useful,score
    def cycle(self):
        bs=self.signals(); spawned=[]
        active=sum(w.get("status") in ("probation","permanent") for w in self.reg["workers"])
        for b in bs:
            if active>=8:break
            if not self.active(b): spawned.append(self.spawn(b)); active+=1
        promoted=[]; retired=[]
        for w in self.reg["workers"]:
            if w.get("status") not in ("probation","permanent"):continue
            jobs,succ,fail,useful,score=self.metrics(w)
            w.update(jobs=jobs,successes=succ,failures=fail,useful_outputs=useful,verified_score=score,updated_at=time.time())
            if w["status"]=="probation" and jobs>=3 and useful>=3 and score>=70:
                w["status"]="permanent"; promoted.append(w["worker_id"])
            elif w["status"]=="probation" and jobs>=5 and fail>=3 and useful==0:
                w["status"]="retired"; retired.append(w["worker_id"])
        write(self.regp,self.reg)
        out={"timestamp":time.time(),"bottlenecks":bs,"spawned":spawned,"promoted":promoted,"retired":retired,
             "permanent":[w for w in self.reg["workers"] if w.get("status")=="permanent"],
             "probation":[w for w in self.reg["workers"] if w.get("status")=="probation"],
             "policy":{"max_active_workers":8,"profit_must_be_observed":True,
             "permanent_requires_verified_outcomes":True,"financial_gates_unchanged":True}}
        write(STATE/"latest.json",out); return out

def run():
    f=Factory()
    while True:
        try:f.cycle()
        except Exception as e:write(STATE/"error.json",{"timestamp":time.time(),"error":repr(e)})
        time.sleep(300)
if __name__=="__main__":
    import sys
    if "--once" in sys.argv:print(json.dumps(Factory().cycle(),indent=2))
    else:run()
