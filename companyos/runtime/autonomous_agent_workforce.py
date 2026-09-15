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
