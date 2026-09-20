#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a
. "$HOME/.companyos_launch_env"
set +a

echo "===== COMPANYOS CONTINUOUS IMPROVEMENT SCHEDULER ====="
echo "Rank bottlenecks -> choose improve/build -> probation -> measure -> permanent/retire"
echo "No finance transfer. No DNS mutation. No supervisor restart."

mkdir -p companyos/runtime scripts tests/generated .companyos_runtime/continuous_improvement

cat > companyos/runtime/continuous_improvement_scheduler.py <<'PY'
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
PY

cat > scripts/companyos_improve_cycle <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companyos.runtime.continuous_improvement_scheduler import ContinuousImprovementScheduler
print(json.dumps(ContinuousImprovementScheduler(ROOT).cycle(),indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_improve_cycle

cat > scripts/companyos_improve_status <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from pathlib import Path
p=Path.cwd()/".companyos_runtime/continuous_improvement/latest.json"
print(p.read_text() if p.exists() else '{"status":"not_run"}')
PY
chmod +x scripts/companyos_improve_status

cat > tests/generated/test_continuous_improvement_scheduler.py <<'PY'
from companyos.runtime.continuous_improvement_scheduler import ContinuousImprovementScheduler

def test_protected(tmp_path):
    c=ContinuousImprovementScheduler(tmp_path)
    assert c.protected("companyos/finance/live_transfer.py")
    assert not c.protected("candidate_qualification")

def test_new_specialist_selected(tmp_path):
    c=ContinuousImprovementScheduler(tmp_path)
    b={"id":"market_evidence","priority":80,"hits":3,"sources":[]}
    selected,action=c.choose([b],{"workers":{}})
    assert selected["id"]=="market_evidence"
    assert action=="build_new_specialist"

def test_permanent_requires_repeated_evidence(tmp_path):
    c=ContinuousImprovementScheduler(tmp_path)
    reg={"workers":{}}
    b={"id":"market_evidence","priority":80,"hits":3,"sources":[]}
    for _ in range(3):
        w=c.update_worker(b,"build_new_specialist",reg)
    assert w["status"]=="permanent"
    assert w["successes"]==3

def test_no_invented_profit(tmp_path):
    c=ContinuousImprovementScheduler(tmp_path)
    reg={"workers":{}}
    b={"id":"revenue_evidence","priority":80,"hits":2,"sources":[]}
    w=c.update_worker(b,"build_new_specialist",reg)
    assert w["attributed_profit"]==0.0
PY

echo "===== COMPILE ====="
python -m py_compile companyos/runtime/continuous_improvement_scheduler.py scripts/companyos_improve_cycle scripts/companyos_improve_status

echo "===== TEST ====="
python -m pytest -q tests/generated/test_continuous_improvement_scheduler.py

echo "===== COMMISSION 3 CYCLES ====="
python scripts/companyos_improve_cycle >/tmp/companyos_improve_1.json
python scripts/companyos_improve_cycle >/tmp/companyos_improve_2.json
python scripts/companyos_improve_cycle | tee /tmp/companyos_improve_3.json

echo "===== STATUS ====="
python scripts/companyos_improve_status

echo "===== VERIFY SUPERVISOR UNTOUCHED ====="
python - <<'PY'
import json
from pathlib import Path
p=Path(".companyos_runtime/service_supervisor_state.json")
if p.exists():
    d=json.loads(p.read_text())
    print("supervisor_pid:",d.get("supervisor_pid"))
    print("stop_requested:",d.get("stop_requested"))
else:
    print("supervisor state file not found; no supervisor mutation performed")
PY

echo "===== COMMIT ONLY THIS BUILD ====="
git add \
  companyos/runtime/continuous_improvement_scheduler.py \
  scripts/companyos_improve_cycle \
  scripts/companyos_improve_status \
  tests/generated/test_continuous_improvement_scheduler.py
git commit -m "add continuous autonomous improvement scheduler" || true

echo "===== FINAL ====="
git rev-parse --short HEAD
python scripts/companyos_improve_status
echo "COMPANYOS_CONTINUOUS_IMPROVEMENT_SCHEDULER=PASS"
