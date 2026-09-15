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
