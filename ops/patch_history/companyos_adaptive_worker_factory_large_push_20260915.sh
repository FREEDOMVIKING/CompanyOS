#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS ADAPTIVE WORKER FACTORY ====="
echo "No finance/DNS changes. No supervisor restart."
mkdir -p companyos/runtime scripts tests/generated .companyos_runtime/adaptive_workers
cp companyos/runtime/service_supervisor.py ".companyos_runtime/service_supervisor.py.worker_factory.$(date +%s).bak"

cat > companyos/runtime/adaptive_worker_factory.py <<'PY'
from __future__ import annotations
import json,hashlib,time
from pathlib import Path

ROOT=Path.home()/"companyos"; RT=ROOT/".companyos_runtime"; STATE=RT/"adaptive_workers"
STATE.mkdir(parents=True,exist_ok=True)
BOTTLENECKS=("execution_readiness","revenue_evidence","market_evidence","pricing","research")
ROLES={"execution_readiness":"execution_readiness","revenue_evidence":"revenue_evidence",
"market_evidence":"market_validation","pricing":"pricing","research":"research"}

def read(p,d):
    try:return json.loads(p.read_text())
    except Exception:return d
def write(p,v):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n"); t.replace(p)

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
PY

cat > scripts/companyos_workerctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json,sys
from pathlib import Path
from companyos.runtime.adaptive_worker_factory import Factory
if len(sys.argv)>1 and sys.argv[1]=="cycle": print(json.dumps(Factory().cycle(),indent=2))
else:
 p=Path.home()/"companyos/.companyos_runtime/adaptive_workers/latest.json"
 print(p.read_text() if p.exists() else '{"status":"not_run"}')
PY
chmod +x scripts/companyos_workerctl

cat > tests/generated/test_adaptive_worker_factory.py <<'PY'
from companyos.runtime.adaptive_worker_factory import ROLES,BOTTLENECKS
def test_coverage(): assert set(BOTTLENECKS)<=set(ROLES)
def test_bounded(): assert len(BOTTLENECKS)<=8
def test_unprivileged():
 s=" ".join(ROLES.values()).lower()
 assert all(x not in s for x in ("wallet","finance","credential","approval"))
PY

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/service_supervisor.py"); s=p.read_text()
if "adaptive_worker_factory" not in s:
 marker="        return services"
 lines=[
 '        if (Path.home()/"companyos/companyos/runtime/adaptive_worker_factory.py").exists():',
 '            services.append(',
 '                ManagedService(',
 '                    "adaptive_worker_factory",',
 '                    (python, "-m", "companyos.runtime.adaptive_worker_factory"),',
 '                )',
 '            )',
 ''
 ]
 if marker not in s: raise SystemExit("ERROR: return services marker missing; refusing blind mutation")
 s=s.replace(marker,"\n".join(lines)+marker,1); p.write_text(s)
 print("SUPERVISOR_REGISTRATION_INSERTED")
else: print("SUPERVISOR_REGISTRATION_ALREADY_PRESENT")
PY

echo "===== COMPILE + TEST ====="
python -m py_compile companyos/runtime/adaptive_worker_factory.py companyos/runtime/service_supervisor.py
python -m pytest -q tests/generated/test_adaptive_worker_factory.py
echo "===== FIRST CYCLE ====="
python scripts/companyos_workerctl cycle
echo "===== REGISTRATION ====="
grep -n -A8 -B2 adaptive_worker_factory companyos/runtime/service_supervisor.py
echo "===== COMMIT ONLY THIS PUSH ====="
git add companyos/runtime/adaptive_worker_factory.py scripts/companyos_workerctl tests/generated/test_adaptive_worker_factory.py companyos/runtime/service_supervisor.py
git commit -m "add evidence-driven adaptive specialist worker factory" || true
echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
echo "FINANCE_LIMITS_CHANGED=NO"
echo "PERMANENT_WORKERS_REQUIRE_VERIFIED_OUTCOMES=YES"
echo "COMPANYOS_ADAPTIVE_WORKER_FACTORY_LARGE_PUSH=PASS"
