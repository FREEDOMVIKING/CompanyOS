#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a

echo "===== COMPANYOS AUTONOMOUS AGENT WORKFORCE LARGE PUSH ====="
echo "Dynamic specialists + parallel scheduling + measured promotion/retirement."
echo "No finance transfer. No credential delegation. No DNS mutation. No supervisor restart."
mkdir -p companyos/runtime scripts tests/generated .companyos_runtime/agent_workforce

cat > companyos/runtime/autonomous_agent_workforce.py <<'PY'
from __future__ import annotations
import concurrent.futures, hashlib, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path

PROTECTED={"finance","wallet","credential","secret","approval","dns","contract","payment","transfer"}
SAFE_ROLES={"research","market_validation","product_builder","software_builder","sales_research",
            "pricing","competitive_analysis","website_builder","debugging","performance_analysis",
            "evidence_analysis","lead_research","operations_analysis"}
def now(): return datetime.now(timezone.utc).isoformat()
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,t=tempfile.mkstemp(dir=str(p.parent),prefix=p.name+".")
    with os.fdopen(fd,"w") as f:
        json.dump(d,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
    os.replace(t,p)
def read_json(p,d):
    try:return json.loads(Path(p).read_text())
    except:return d
def aid(role):
    return role+"-"+hashlib.sha256((role+now()).encode()).hexdigest()[:10]

class AgentWorkforce:
    """Measured autonomous specialist workforce.

    Agents begin probationary. Promotion requires repeat work and positive
    attributable value. Workforce status never grants new protected authority.
    """
    def __init__(self,root):
        self.root=Path(root);self.rt=self.root/".companyos_runtime"/"agent_workforce"
        self.registry_path=self.rt/"registry.json";self.rt.mkdir(parents=True,exist_ok=True)
        self.registry=read_json(self.registry_path,{"agents":{}})

    def create(self,role,purpose):
        role=str(role).lower().strip().replace(" ","_")
        if role not in SAFE_ROLES:return {"created":False,"reason":"role_not_in_safe_catalog"}
        text=(role+" "+str(purpose)).lower()
        if any(x in text for x in PROTECTED):return {"created":False,"reason":"protected_authority_requested"}
        x={"agent_id":aid(role),"role":role,"purpose":str(purpose)[:500],"status":"probation",
           "created_at":now(),"jobs":0,"successes":0,"failures":0,"useful_outputs":0,
           "attributed_profit":0.0,"score":0.0,"permissions":["read_workspace","write_agent_artifacts"]}
        self.registry["agents"][x["agent_id"]]=x;self.save();return {"created":True,"agent":x}

    def save(self):write_json(self.registry_path,self.registry)

    def record(self,agent_id,success,useful=False,attributed_profit=0.0):
        a=self.registry["agents"].get(agent_id)
        if not a:return {"updated":False,"reason":"unknown_agent"}
        a["jobs"]+=1;a["successes"]+=int(bool(success));a["failures"]+=int(not success)
        a["useful_outputs"]+=int(bool(useful))
        # Profit is accepted only as an upstream verified attribution signal.
        a["attributed_profit"]=round(a["attributed_profit"]+max(0,float(attributed_profit or 0)),2)
        reliability=a["successes"]/max(1,a["jobs"])
        usefulness=a["useful_outputs"]/max(1,a["jobs"])
        repeat=min(a["jobs"]/10,1)
        profit=min(a["attributed_profit"]/500,1)
        a["score"]=round(100*(.40*reliability+.25*usefulness+.20*repeat+.15*profit),2)
        # Permanent promotion requires repeated work, high reliability/usefulness,
        # and either verified profit or substantial repeated useful work.
        if a["jobs"]>=8 and reliability>=.85 and usefulness>=.70 and (a["attributed_profit"]>0 or a["jobs"]>=12):
            a["status"]="permanent"
        elif a["jobs"]>=6 and reliability<.50:
            a["status"]="retired"
        elif a["status"]=="permanent" and a["jobs"]>=15 and reliability<.65:
            a["status"]="demoted"
        a["updated_at"]=now();self.save();return {"updated":True,"agent":a}

    def select(self,role):
        xs=[a for a in self.registry["agents"].values() if a["role"]==role and a["status"]!="retired"]
        return max(xs,key=lambda a:(a["status"]=="permanent",a["score"]),default=None)

    def portfolio(self):
        xs=list(self.registry["agents"].values())
        return {"total":len(xs),"permanent":sum(a["status"]=="permanent" for a in xs),
                "probation":sum(a["status"]=="probation" for a in xs),
                "retired":sum(a["status"]=="retired" for a in xs),
                "agents":sorted(xs,key=lambda a:a["score"],reverse=True)}

class ParallelDelegator:
    def __init__(self,root,max_workers=4):
        self.root=Path(root);self.workforce=AgentWorkforce(root);self.max_workers=max(1,min(int(max_workers),8))
    def plan(self,opportunity):
        gaps=opportunity.get("gaps") or ["research","market_validation","pricing","competitive_analysis"]
        roles=[]
        for g in gaps:
            g=str(g).lower().replace(" ","_")
            if g in SAFE_ROLES and g not in roles:roles.append(g)
        return roles[:8]
    def delegate(self,opportunity,worker):
        roles=self.plan(opportunity);jobs=[]
        for role in roles:
            a=self.workforce.select(role)
            if not a:
                c=self.workforce.create(role,"profit-directed opportunity work")
                if not c.get("created"):continue
                a=c["agent"]
            jobs.append((a,role))
        results=[]
        def run(pair):
            a,role=pair
            try:
                result=worker(a,opportunity)
                success=bool(result.get("success"));useful=bool(result.get("useful"))
                # No worker may self-report trusted profit. Verified attribution is a separate input.
                self.workforce.record(a["agent_id"],success,useful,0)
                return {"agent_id":a["agent_id"],"role":role,**result}
            except Exception as e:
                self.workforce.record(a["agent_id"],False,False,0)
                return {"agent_id":a["agent_id"],"role":role,"success":False,"error":str(e)[:500]}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            for r in ex.map(run,jobs):results.append(r)
        report={"timestamp":now(),"opportunity_id":opportunity.get("id"),"parallel_workers":self.max_workers,
                "results":results,"workforce":self.workforce.portfolio()}
        write_json(self.workforce.rt/"latest_delegation.json",report);return report
PY

cat > scripts/companyos_agentctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companyos.runtime.autonomous_agent_workforce import AgentWorkforce
p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
sub.add_parser("status")
c=sub.add_parser("create");c.add_argument("--role",required=True);c.add_argument("--purpose",default="specialist work")
r=sub.add_parser("record");r.add_argument("--agent",required=True);r.add_argument("--success",action="store_true");r.add_argument("--useful",action="store_true");r.add_argument("--verified-profit",type=float,default=0)
a=p.parse_args();w=AgentWorkforce(ROOT)
if a.cmd=="status":o=w.portfolio()
elif a.cmd=="create":o=w.create(a.role,a.purpose)
else:o=w.record(a.agent,a.success,a.useful,a.verified_profit)
print(json.dumps(o,indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_agentctl

cat > tests/generated/test_autonomous_agent_workforce.py <<'PY'
from companyos.runtime.autonomous_agent_workforce import AgentWorkforce,ParallelDelegator
def test_protected_role_rejected(tmp_path):
 assert not AgentWorkforce(tmp_path).create("research","wallet transfer research")["created"]
def test_agent_starts_probation(tmp_path):
 r=AgentWorkforce(tmp_path).create("research","market research");assert r["agent"]["status"]=="probation"
def test_good_agent_becomes_permanent(tmp_path):
 w=AgentWorkforce(tmp_path);a=w.create("pricing","pricing work")["agent"]["agent_id"]
 for i in range(8):w.record(a,True,True,10 if i==7 else 0)
 assert w.registry["agents"][a]["status"]=="permanent"
def test_bad_agent_retires(tmp_path):
 w=AgentWorkforce(tmp_path);a=w.create("debugging","debug")["agent"]["agent_id"]
 for _ in range(6):w.record(a,False,False,0)
 assert w.registry["agents"][a]["status"]=="retired"
def test_parallel_delegation(tmp_path):
 d=ParallelDelegator(tmp_path,4)
 r=d.delegate({"id":"o","gaps":["research","pricing","competitive_analysis"]},lambda a,o:{"success":True,"useful":True})
 assert len(r["results"])==3 and all(x["success"] for x in r["results"])
def test_worker_cannot_self_report_profit(tmp_path):
 d=ParallelDelegator(tmp_path,2)
 r=d.delegate({"id":"o","gaps":["research"]},lambda a,o:{"success":True,"useful":True,"attributed_profit":999999})
 a=next(iter(d.workforce.registry["agents"].values()))
 assert a["attributed_profit"]==0
PY

echo "===== COMPILE + TEST ====="
python -m py_compile companyos/runtime/autonomous_agent_workforce.py scripts/companyos_agentctl
python -m pytest -q tests/generated/test_autonomous_agent_workforce.py tests/generated/test_market_evidence_engine.py tests/generated/test_post_launch_revenue_loop.py

echo "===== SAFE PARALLEL COMMISSIONING ====="
python - <<'PY'
from pathlib import Path
import json
from companyos.runtime.autonomous_agent_workforce import ParallelDelegator
d=ParallelDelegator(Path.cwd(),4)
o={"id":"agent-workforce-commissioning","gaps":["research","market_validation","pricing","competitive_analysis"]}
r=d.delegate(o,lambda a,o:{"success":True,"useful":True,"artifact":"commissioning-only"})
print(json.dumps(r,indent=2))
assert len(r["results"])==4
assert all(x["success"] for x in r["results"])
print("PARALLEL_AGENT_COMMISSIONING=PASS")
PY

echo "===== WORKFORCE STATUS ====="
python scripts/companyos_agentctl status

echo "===== COMMIT ONLY THIS PUSH ====="
git add companyos/runtime/autonomous_agent_workforce.py scripts/companyos_agentctl tests/generated/test_autonomous_agent_workforce.py
git commit -m "add measured autonomous specialist agent workforce" || true
echo "===== FINAL ====="
git rev-parse --short HEAD
git status --short
echo "COMPANYOS_AUTONOMOUS_AGENT_WORKFORCE=PASS"
