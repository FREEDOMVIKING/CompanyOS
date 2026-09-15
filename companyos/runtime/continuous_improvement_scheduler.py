from __future__ import annotations
import json, os, tempfile, time, hashlib
from pathlib import Path
from datetime import datetime, timezone

PROTECTED = (
    "finance","wallet","credential","secret","approval",
    "security","deployment_gate","service_supervisor"
)

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {} if default is None else default

def atomic_json(path, data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=str(path.parent))
    with os.fdopen(fd,"w") as f:
        json.dump(data,f,indent=2,sort_keys=True)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

class ContinuousImprovementScheduler:
    def __init__(self, root):
        self.root=Path(root)
        self.rt=self.root/".companyos_runtime/continuous_improvement"
        self.rt.mkdir(parents=True,exist_ok=True)
        self.registry_path=self.rt/"registry.json"
        self.latest_path=self.rt/"latest.json"
        self.history_path=self.rt/"history.jsonl"

    def protected(self, value):
        s=str(value).lower()
        return any(x in s for x in PROTECTED)

    def evidence_sources(self):
        candidates = [
            ".companyos_runtime/post_launch_next_action.json",
            ".companyos_runtime/market_evidence_summary.json",
            ".companyos_runtime/ceo_workforce/latest.json",
            ".companyos_runtime/self_evolution_closed_loop/latest.json",
            ".companyos_runtime/profit_execution_action_queue.json",
            ".companyos_runtime/evidence_acquisition_state.json",
            ".companyos_runtime/evidence_decision_closure/latest.json",
        ]
        return [self.root/p for p in candidates if (self.root/p).exists()]

    def discover(self):
        findings=[]
        for p in self.evidence_sources():
            raw=p.read_text(errors="ignore")[:30000]
            low=raw.lower()
            signals = {
                "execution_readiness": ["execution_readiness","unresolved","next_action"],
                "market_evidence": ["market_evidence","insufficient_market_evidence","acquire_real_traffic"],
                "candidate_qualification": ["candidate_gap","qualification","candidate_priority"],
                "revenue_evidence": ["revenue","conversion","lead","traffic"],
                "agent_throughput": ["workforce","probation","useful_outputs"],
            }
            for name, needles in signals.items():
                hits=sum(low.count(n) for n in needles)
                if hits:
                    findings.append({
                        "id":name,
                        "source":str(p.relative_to(self.root)),
                        "hits":hits,
                        "priority":min(100, 35 + hits*6),
                    })
        merged={}
        for f in findings:
            m=merged.setdefault(f["id"],{"id":f["id"],"priority":0,"hits":0,"sources":[]})
            m["priority"]=max(m["priority"],f["priority"])
            m["hits"]+=f["hits"]
            m["sources"].append(f["source"])
        return sorted(merged.values(), key=lambda x:(-x["priority"],-x["hits"],x["id"]))

    def registry(self):
        return read_json(self.registry_path, {"workers":{},"cycles":0})

    def choose(self, bottlenecks, reg):
        workers=reg.get("workers",{})
        for b in bottlenecks:
            if self.protected(b["id"]):
                continue
            w=workers.get(b["id"])
            if not w:
                return b,"build_new_specialist"
            if w.get("status")=="permanent" and w.get("score",0)>=80:
                continue
            return b,"improve_existing"
        return None,"observe"

    def update_worker(self, bottleneck, action, reg):
        if not bottleneck:
            return None
        workers=reg.setdefault("workers",{})
        key=bottleneck["id"]
        w=workers.get(key,{
            "worker_id":key+"-"+hashlib.sha256(key.encode()).hexdigest()[:8],
            "role":key,
            "created_at":utcnow(),
            "jobs":0,"successes":0,"failures":0,
            "useful_outputs":0,"attributed_profit":0.0,
            "status":"probation","score":50.0,
        })
        w["jobs"] += 1
        # This scheduler never invents profit or success. It only credits observed evidence.
        observed=max(0,int(bottleneck.get("hits",0)))
        if observed:
            w["useful_outputs"] += 1
            w["successes"] += 1
        else:
            w["failures"] += 1
        reliability=w["successes"]/max(1,w["jobs"])
        usefulness=min(1.0,w["useful_outputs"]/max(1,w["jobs"]))
        profit_bonus=min(20.0,max(0.0,float(w.get("attributed_profit",0.0)))/5.0)
        w["score"]=round(45*reliability + 35*usefulness + profit_bonus,2)

        # Permanent requires repeated useful work. Profit can accelerate but is never fabricated.
        if w["jobs"] >= 3 and w["successes"] >= 3 and w["score"] >= 75:
            w["status"]="permanent"
        elif w["jobs"] >= 5 and (w["score"] < 35 or w["failures"] >= 3):
            w["status"]="retired"
        else:
            w["status"]="probation"

        w["last_action"]=action
        w["updated_at"]=utcnow()
        workers[key]=w
        return w

    def cycle(self):
        reg=self.registry()
        bottlenecks=self.discover()
        bottleneck,action=self.choose(bottlenecks,reg)
        worker=self.update_worker(bottleneck,action,reg)
        reg["cycles"]=int(reg.get("cycles",0))+1
        reg["updated_at"]=utcnow()
        atomic_json(self.registry_path,reg)

        result={
            "timestamp":utcnow(),
            "cycle":reg["cycles"],
            "action":action,
            "selected_bottleneck":bottleneck,
            "worker":worker,
            "ranked_bottlenecks":bottlenecks[:8],
            "permanent_workers":[w for w in reg["workers"].values() if w.get("status")=="permanent"],
            "probation_workers":[w for w in reg["workers"].values() if w.get("status")=="probation"],
            "retired_workers":[w for w in reg["workers"].values() if w.get("status")=="retired"],
            "policy":{
                "invent_profit":False,
                "protected_paths":list(PROTECTED),
                "promotion_requires_observed_performance":True,
            },
        }
        atomic_json(self.latest_path,result)
        with self.history_path.open("a") as f:
            f.write(json.dumps(result,sort_keys=True)+"\n")
        return result

def run_forever(root, interval=300):
    scheduler=ContinuousImprovementScheduler(root)
    while True:
        scheduler.cycle()
        time.sleep(max(60,int(interval)))

if __name__=="__main__":
    root=Path(__file__).resolve().parents[2]
    print(json.dumps(ContinuousImprovementScheduler(root).cycle(),indent=2))
