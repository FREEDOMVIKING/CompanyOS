#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a

echo "===== COMPANYOS CEO -> AUTONOMOUS WORKFORCE LARGE PUSH ====="
echo "Profit-directed delegation, adaptive parallelism, permanent-agent reuse."
echo "No financial transfers. No credential delegation. No DNS mutation. No supervisor restart."

mkdir -p companyos/runtime scripts tests/generated .companyos_runtime/ceo_workforce

cat > companyos/runtime/ceo_workforce_orchestrator.py <<'PY'
from __future__ import annotations
import json, math, os, tempfile
from datetime import datetime, timezone
from pathlib import Path
from companyos.runtime.autonomous_agent_workforce import AgentWorkforce, ParallelDelegator

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p, default=None):
    try: return json.loads(Path(p).read_text())
    except Exception: return {} if default is None else default
def write_json(p, data):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(p.parent),prefix=p.name+".")
    with os.fdopen(fd,"w") as f:
        json.dump(data,f,indent=2,sort_keys=True); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,p)

ROLE_MAP = {
 "research":["research"],
 "evidence":["evidence_analysis","market_validation"],
 "market":["market_validation","competitive_analysis"],
 "pricing":["pricing"],
 "build":["product_builder","software_builder"],
 "software":["software_builder","debugging"],
 "website":["website_builder"],
 "sales":["sales_research","lead_research"],
 "lead":["lead_research","sales_research"],
 "debug":["debugging"],
 "performance":["performance_analysis"],
 "operations":["operations_analysis"],
}
DEFAULT_ROLES=["research","market_validation","pricing","competitive_analysis"]

class CEOWorkforceOrchestrator:
    def __init__(self, root):
        self.root=Path(root)
        self.runtime=self.root/".companyos_runtime"
        self.state_dir=self.runtime/"ceo_workforce"
        self.state_dir.mkdir(parents=True,exist_ok=True)
        self.workforce=AgentWorkforce(root)

    def _candidate_files(self):
        return [
          self.runtime/"profit_opportunity_latest.json",
          self.runtime/"profit_opportunity_state.json",
          self.runtime/"selected_profit_opportunity.json",
          self.runtime/"post_launch_next_action.json",
        ]

    def load_opportunity(self):
        for p in self._candidate_files():
            x=read_json(p,{})
            if not x: continue
            for key in ("selected","opportunity","candidate"):
                if isinstance(x.get(key),dict): x=x[key]
            if x.get("id") or x.get("opportunity_id") or x.get("title"):
                return x
        return {"id":"ceo-workforce-commissioning","title":"CompanyOS workforce commissioning",
                "expected_profit":None,"confidence":0.5,
                "next_action":"research validate pricing competitive analysis"}

    def derive_roles(self, opp):
        explicit=opp.get("gaps")
        if isinstance(explicit,list):
            roles=[]
            for r in explicit:
                r=str(r).lower().replace(" ","_")
                if r in self.workforce.registry.get("agents",{}) : continue
                if r in __import__("companyos.runtime.autonomous_agent_workforce",fromlist=["SAFE_ROLES"]).SAFE_ROLES and r not in roles:
                    roles.append(r)
            if roles:return roles[:8]
        text=" ".join(str(opp.get(k,"")) for k in ("title","description","reason","next_action","bottleneck")).lower()
        roles=[]
        for token, mapped in ROLE_MAP.items():
            if token in text:
                for r in mapped:
                    if r not in roles: roles.append(r)
        return (roles or DEFAULT_ROLES)[:8]

    def priority(self, opp):
        # Missing numbers are not invented.
        profit=opp.get("expected_profit")
        confidence=opp.get("confidence")
        readiness=opp.get("readiness")
        score=0.0
        if isinstance(profit,(int,float)): score += min(max(profit,0),10000)/100
        if isinstance(confidence,(int,float)): score += max(0,min(confidence,1))*35
        if isinstance(readiness,(int,float)): score += max(0,min(readiness,1))*25
        if opp.get("public_url"): score += 10
        return round(score,2)

    def worker_budget(self, priority, roles):
        # Adaptive but bounded: 2..8, never unbounded agent spawning.
        n=2 + int(min(max(priority,0),100)//20)
        return max(1,min(8,len(roles),n))

    def _safe_worker(self, agent, opp):
        # This layer delegates analysis/build preparation only. Existing downstream
        # systems remain responsible for model execution, deployment and approvals.
        role=agent["role"]
        packet={
          "timestamp":now(),"agent_id":agent["agent_id"],"role":role,
          "opportunity_id":opp.get("id") or opp.get("opportunity_id"),
          "objective":opp.get("next_action") or opp.get("title"),
          "status":"work_packet_created",
          "requires_execution_bridge":True,
          "protected_authority_granted":False,
        }
        p=self.state_dir/"work_packets"/(agent["agent_id"]+".json")
        write_json(p,packet)
        return {"success":True,"useful":True,"artifact":str(p.relative_to(self.root)),
                "work_packet":packet}

    def run(self, opportunity=None):
        opp=dict(opportunity or self.load_opportunity())
        opp["id"]=opp.get("id") or opp.get("opportunity_id") or "unknown-opportunity"
        roles=self.derive_roles(opp)
        priority=self.priority(opp)
        workers=self.worker_budget(priority,roles)
        selected_roles=roles[:workers]
        opp["gaps"]=selected_roles
        delegation=ParallelDelegator(self.root,workers).delegate(opp,self._safe_worker)
        result={"timestamp":now(),"opportunity_id":opp["id"],"title":opp.get("title"),
                "priority_score":priority,"requested_roles":roles,
                "active_roles":selected_roles,"worker_budget":workers,
                "delegation":delegation,
                "next_stage":"execution_bridge",
                "financial_authority_delegated":False,
                "credential_authority_delegated":False}
        write_json(self.state_dir/"latest.json",result)
        with (self.state_dir/"ledger.jsonl").open("a") as f:
            f.write(json.dumps(result,sort_keys=True)+"\n")
        return result
PY

cat > scripts/companyos_ceoworkforce <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companyos.runtime.ceo_workforce_orchestrator import CEOWorkforceOrchestrator
print(json.dumps(CEOWorkforceOrchestrator(ROOT).run(),indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_ceoworkforce

cat > scripts/companyos_ceoworkforce_status <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json
from pathlib import Path
p=Path.cwd()/".companyos_runtime/ceo_workforce/latest.json"
print(p.read_text() if p.exists() else json.dumps({"status":"not_run"},indent=2))
PY
chmod +x scripts/companyos_ceoworkforce_status

cat > tests/generated/test_ceo_workforce_orchestrator.py <<'PY'
from companyos.runtime.ceo_workforce_orchestrator import CEOWorkforceOrchestrator
def test_profit_priority_does_not_invent(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 assert c.priority({"expected_profit":None,"confidence":None})==0
def test_adaptive_workers_are_bounded(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 assert c.worker_budget(1000,list("abcdefghij"))<=8
def test_ceo_creates_work_packets(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 r=c.run({"id":"opp1","title":"research pricing market","gaps":["research","pricing","market_validation"],"confidence":.8})
 assert r["opportunity_id"]=="opp1"
 assert len(r["delegation"]["results"])>=1
 assert all(x["success"] for x in r["delegation"]["results"])
def test_no_authority_delegation(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 r=c.run({"id":"opp2","title":"market research","gaps":["research"]})
 assert r["financial_authority_delegated"] is False
 assert r["credential_authority_delegated"] is False
def test_permanent_agent_reused(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 a=c.workforce.create("research","profit-directed research")["agent"]["agent_id"]
 for i in range(8): c.workforce.record(a,True,True,10 if i==7 else 0)
 r=c.run({"id":"opp3","gaps":["research"],"title":"research"})
 assert r["delegation"]["results"][0]["agent_id"]==a
PY

echo "===== COMPILE ====="
python -m py_compile companyos/runtime/ceo_workforce_orchestrator.py scripts/companyos_ceoworkforce

echo "===== TEST CEO + AGENT STACK ====="
python -m pytest -q \
 tests/generated/test_autonomous_agent_workforce.py \
 tests/generated/test_ceo_workforce_orchestrator.py \
 tests/generated/test_market_evidence_engine.py \
 tests/generated/test_post_launch_revenue_loop.py

echo "===== REAL CEO DELEGATION RUN ====="
python scripts/companyos_ceoworkforce | tee .companyos_runtime/ceo_workforce_commissioning.json

echo "===== ASSERTIONS ====="
python - <<'PY'
import json
from pathlib import Path
p=Path(".companyos_runtime/ceo_workforce/latest.json")
r=json.loads(p.read_text())
assert 1 <= r["worker_budget"] <= 8
assert r["financial_authority_delegated"] is False
assert r["credential_authority_delegated"] is False
assert r["delegation"]["results"]
assert all(x.get("success") for x in r["delegation"]["results"])
print("CEO_WORKFORCE_INTEGRATION=PASS")
print("OPPORTUNITY_ID="+str(r["opportunity_id"]))
print("WORKER_BUDGET="+str(r["worker_budget"]))
print("ACTIVE_ROLES="+",".join(r["active_roles"]))
PY

echo "===== WORKFORCE ====="
python scripts/companyos_agentctl status

echo "===== COMMIT ONLY THIS PUSH ====="
git add companyos/runtime/ceo_workforce_orchestrator.py scripts/companyos_ceoworkforce scripts/companyos_ceoworkforce_status tests/generated/test_ceo_workforce_orchestrator.py
git commit -m "connect CEO opportunity flow to autonomous specialist workforce" || true

echo "===== SUPERVISOR UNTOUCHED ====="
python - <<'PY'
import json
from pathlib import Path
p=Path(".companyos_runtime/service_supervisor_state.json")
if p.exists():
 r=json.loads(p.read_text())
 print("running:",r.get("running"))
 print("supervisor_alive:",r.get("supervisor_alive"))
 print("stop_requested:",r.get("stop_requested"))
else: print("state unavailable; no restart attempted")
PY

echo "===== FINAL ====="
git rev-parse --short HEAD
git status --short
echo "COMPANYOS_CEO_AGENT_ORCHESTRATION=PASS"
