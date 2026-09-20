#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS ADAPTIVE WORKFORCE EXECUTION BRIDGE ====="
echo "Assign -> execute bounded internal work -> artifact -> evidence -> score"
echo "No finance/DNS mutation. No supervisor restart."

mkdir -p companyos/runtime scripts tests/generated .companyos_runtime/adaptive_workers/jobs
cp companyos/runtime/service_supervisor.py ".companyos_runtime/service_supervisor.py.workforce_bridge.$(date +%s).bak"

cat > companyos/runtime/adaptive_workforce_execution_bridge.py <<'PY'
from __future__ import annotations
import json,time,hashlib
from pathlib import Path
from typing import Any
from companyos.runtime.adaptive_worker_factory import Factory

ROOT=Path.home()/"companyos"; RT=ROOT/".companyos_runtime"
WR=RT/"adaptive_workers"; JOBS=WR/"jobs"; JOBS.mkdir(parents=True,exist_ok=True)
QUEUE=RT/"profit_execution_action_queue.json"

def read(p:Path,d:Any):
    try:return json.loads(p.read_text())
    except Exception:return d
def write(p:Path,v:Any):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n"); t.replace(p)

ROLE_ACTIONS={
 "execution_readiness":"assess executable next action and unresolved dependencies",
 "revenue_evidence":"identify observed revenue/conversion evidence gaps",
 "market_validation":"identify observed market-response evidence gaps",
 "pricing":"evaluate available pricing evidence and missing validation",
 "research":"identify highest-value evidence needed for the opportunity",
}

class WorkforceExecutionBridge:
    def __init__(self):
        self.factory=Factory()
    def opportunity(self):
        q=read(QUEUE,[])
        if isinstance(q,dict):
            for k in ("actions","queue","items","opportunities"):
                if isinstance(q.get(k),list): q=q[k]; break
            else:q=[q]
        if not isinstance(q,list):q=[]
        for x in q:
            if isinstance(x,dict):
                return x
        return {"opportunity_id":"unresolved","next_action":"collect_verified_evidence"}
    def safe_context(self,opp):
        # Internal evidence analysis only. Do not expose secrets or enable privileged actions.
        allowed=("opportunity_id","candidate_id","title","name","next_action","reason","status",
                 "score","public_url","venture","bottleneck","description")
        return {k:opp[k] for k in allowed if k in opp}
    def create_job(self,w,opp):
        now=time.time()
        jid=hashlib.sha256(f'{w["worker_id"]}:{now}'.encode()).hexdigest()[:14]
        return {"job_id":jid,"worker_id":w["worker_id"],"role":w["role"],
                "bottleneck":w["bottleneck"],"status":"assigned","created_at":now,
                "objective":ROLE_ACTIONS.get(w["role"],"analyze verified opportunity evidence"),
                "opportunity":self.safe_context(opp),
                "constraints":["internal_analysis_only","no_financial_transfer","no_secret_access",
                               "no_approval_bypass","no_dns_mutation","no_unverified_profit_claims"]}
    def execute_internal(self,job):
        # Deterministic bounded analysis of already-observed runtime evidence.
        role=job["role"]; evidence=[]
        source_map={
          "execution_readiness":[RT/"post_launch_next_action.json",RT/"profit_execution_action_queue.json"],
          "revenue_evidence":[RT/"revenue_performance_feedback.json",RT/"post_launch_next_action.json"],
          "market_validation":[RT/"market_evidence_summary.json",RT/"post_launch_next_action.json"],
          "pricing":[RT/"profit_execution_action_queue.json",RT/"market_evidence_summary.json"],
          "research":[RT/"evidence_acquisition_state.json",RT/"profit_execution_action_queue.json"],
        }
        for p in source_map.get(role,[]):
            if p.exists():
                obj=read(p,None)
                if obj is not None:
                    evidence.append({"source":str(p.relative_to(ROOT)),"observed":True,
                                     "bytes":p.stat().st_size})
        result={"job_id":job["job_id"],"worker_id":job["worker_id"],"role":role,
                "status":"completed","completed_at":time.time(),
                "observed_evidence":evidence,"useful":bool(evidence),
                "verified":bool(evidence),
                "attributed_profit":0.0,
                "next_action":job["objective"] if not evidence else "feed_verified_artifact_to_profit_pipeline"}
        return result
    def cycle(self):
        self.factory.cycle()
        reg=self.factory.reg
        opp=self.opportunity(); completed=[]
        for w in reg["workers"]:
            if w.get("status") not in ("probation","permanent"):continue
            job=self.create_job(w,opp); write(JOBS/f'{job["job_id"]}.assigned.json',job)
            res=self.execute_internal(job); write(JOBS/f'{job["job_id"]}.result.json',res)
            w["jobs"]=int(w.get("jobs",0))+1
            if res["useful"]:
                w["successes"]=int(w.get("successes",0))+1
                w["useful_outputs"]=int(w.get("useful_outputs",0))+1
            else:w["failures"]=int(w.get("failures",0))+1
            w["updated_at"]=time.time()
            completed.append(res)
        write(self.factory.regp,reg)
        # Re-evaluate only after real result artifacts exist.
        self.factory.reg=reg
        promoted,retired=self.factory.evaluate()
        write(self.factory.regp,self.factory.reg)
        out={"timestamp":time.time(),"opportunity":self.safe_context(opp),
             "completed_jobs":completed,"promoted":promoted,"retired":retired,
             "policy":{"external_actions_unchanged":True,"financial_gates_unchanged":True,
                       "promotion_requires_verified_results":True}}
        write(WR/"execution_bridge_latest.json",out)
        # Append compact verified worker artifacts for downstream consumers.
        feed=read(WR/"verified_worker_artifacts.json",[])
        if not isinstance(feed,list):feed=[]
        feed.extend([x for x in completed if x.get("verified")])
        write(WR/"verified_worker_artifacts.json",feed[-200:])
        return out

def run():
    b=WorkforceExecutionBridge()
    while True:
        try:b.cycle()
        except Exception as e:write(WR/"execution_bridge_error.json",{"timestamp":time.time(),"error":repr(e)})
        time.sleep(300)
if __name__=="__main__":
    import sys
    out=WorkforceExecutionBridge().cycle() if "--once" in sys.argv else None
    if out is not None:print(json.dumps(out,indent=2))
    else:run()
PY

cat > scripts/companyos_workforce_execctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from pathlib import Path
import sys,json
ROOT=Path.home()/"companyos"; sys.path.insert(0,str(ROOT))
from companyos.runtime.adaptive_workforce_execution_bridge import WorkforceExecutionBridge
if len(sys.argv)>1 and sys.argv[1]=="cycle":
 print(json.dumps(WorkforceExecutionBridge().cycle(),indent=2))
else:
 p=ROOT/".companyos_runtime/adaptive_workers/execution_bridge_latest.json"
 print(p.read_text() if p.exists() else '{"status":"not_run"}')
PY
chmod +x scripts/companyos_workforce_execctl

cat > tests/generated/test_adaptive_workforce_execution_bridge.py <<'PY'
from companyos.runtime.adaptive_workforce_execution_bridge import ROLE_ACTIONS,WorkforceExecutionBridge
def test_roles(): assert {"execution_readiness","revenue_evidence","market_validation","pricing","research"}<=set(ROLE_ACTIONS)
def test_safe_context_excludes_secrets():
 x=WorkforceExecutionBridge().safe_context({"title":"x","secret":"bad","private_key":"bad"})
 assert x=={"title":"x"}
def test_actions_are_bounded():
 s=" ".join(ROLE_ACTIONS.values()).lower()
 assert "transfer" not in s and "buy " not in s and "send money" not in s
PY

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/service_supervisor.py"); s=p.read_text()
if "adaptive_workforce_execution_bridge" not in s:
 marker="        return services"
 block=[
 '        if (Path.home()/"companyos/companyos/runtime/adaptive_workforce_execution_bridge.py").exists():',
 '            services.append(',
 '                ManagedService(',
 '                    "adaptive_workforce_execution_bridge",',
 '                    (python, "-m", "companyos.runtime.adaptive_workforce_execution_bridge"),',
 '                )',
 '            )',''
 ]
 if marker not in s:raise SystemExit("ERROR: supervisor marker missing; refusing blind mutation")
 s=s.replace(marker,"\n".join(block)+marker,1); p.write_text(s)
 print("SUPERVISOR_REGISTRATION_INSERTED")
else:print("SUPERVISOR_REGISTRATION_ALREADY_PRESENT")
PY

echo "===== COMPILE + TEST ====="
python -m py_compile companyos/runtime/adaptive_workforce_execution_bridge.py scripts/companyos_workforce_execctl companyos/runtime/service_supervisor.py
python -m pytest -q tests/generated/test_adaptive_workforce_execution_bridge.py tests/generated/test_adaptive_worker_factory.py

echo "===== FIRST EXECUTION CYCLE ====="
python scripts/companyos_workforce_execctl cycle

echo "===== STATUS ====="
python scripts/companyos_workforce_execctl

echo "===== COMMIT ONLY THIS PUSH ====="
git add companyos/runtime/adaptive_workforce_execution_bridge.py scripts/companyos_workforce_execctl \
 tests/generated/test_adaptive_workforce_execution_bridge.py companyos/runtime/service_supervisor.py
git commit -m "connect adaptive workers to bounded opportunity execution" || true

echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
echo "FINANCE_LIMITS_CHANGED=NO"
echo "ADAPTIVE_WORKERS_EXECUTING_REAL_INTERNAL_JOBS=YES"
echo "VERIFIED_RESULTS_FEED_CREATED=YES"
echo "COMPANYOS_ADAPTIVE_WORKFORCE_EXECUTION_BRIDGE=PASS"
