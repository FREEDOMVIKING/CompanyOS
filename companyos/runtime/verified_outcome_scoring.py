from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat()

def readj(p,d=None):
    try: return json.loads(Path(p).read_text())
    except Exception: return {} if d is None else d

def writej(p,d):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    fd,t=tempfile.mkstemp(dir=str(p.parent),prefix=p.name+".")
    with os.fdopen(fd,"w") as f:
        json.dump(d,f,indent=2,sort_keys=True); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)

class VerifiedOutcomeScorer:
    def __init__(self,root):
        self.root=Path(root)
        self.rt=self.root/".companyos_runtime/verified_outcomes"
        self.rt.mkdir(parents=True,exist_ok=True)

    def artifacts(self):
        names=[
          ".companyos_runtime/post_launch_next_action.json",
          ".companyos_runtime/market_evidence_summary.json",
          ".companyos_runtime/profit_execution_action_queue.json",
          ".companyos_runtime/evidence_acquisition_state.json",
          ".companyos_runtime/evidence_decision_closure/latest.json",
          ".companyos_runtime/ceo_workforce/latest.json",
          ".companyos_runtime/continuous_improvement/latest.json",
        ]
        return [(n,self.root/n) for n in names if (self.root/n).exists()]

    def collect(self):
        signals=[]
        for name,p in self.artifacts():
            try: data=readj(p,{})
            except Exception: continue
            raw=json.dumps(data).lower()
            # Only observable outcome classes. Presence alone is not revenue proof.
            classes=[]
            if any(x in raw for x in ['"status": "published"','"site_reachable": true','"http_status": 200']):
                classes.append(("deployment_or_reachability",15))
            if any(x in raw for x in ['"observed": true','"evidence_quality": "verified"','"requires_real_evidence": false']):
                classes.append(("verified_evidence",20))
            if any(x in raw for x in ['"lead_count":','"leads": [','"conversion_count":','"conversions": [']):
                classes.append(("lead_or_conversion_artifact",15))
            if any(x in raw for x in ['"decision": "advance"','"status": "qualified"','"execution_ready": true']):
                classes.append(("opportunity_advanced",20))
            # Revenue is credited only when an explicit observed/verified revenue marker exists.
            if ('"observed_revenue"' in raw or '"verified_revenue"' in raw) and not ('"observed_revenue": null' in raw):
                classes.append(("verified_revenue_marker",30))
            for cls,weight in classes:
                signals.append({"source":name,"class":cls,"weight":weight})
        # deduplicate class+source
        seen=set(); unique=[]
        for s in signals:
            k=(s["source"],s["class"])
            if k not in seen: seen.add(k); unique.append(s)
        return unique

    def evaluate_worker(self,w,signals):
        role=str(w.get("role","")).lower()
        relevant=[]
        mapping={
          "candidate_qualification":{"opportunity_advanced","verified_evidence"},
          "execution_readiness":{"opportunity_advanced","deployment_or_reachability","verified_evidence"},
          "market_evidence":{"verified_evidence","lead_or_conversion_artifact"},
          "revenue_evidence":{"lead_or_conversion_artifact","verified_revenue_marker"},
          "agent_throughput":{"opportunity_advanced","deployment_or_reachability","verified_evidence"},
        }
        wanted=mapping.get(role,set())
        relevant=[s for s in signals if s["class"] in wanted]
        outcome_score=min(100,sum(s["weight"] for s in relevant))
        jobs=max(1,int(w.get("jobs",0)))
        failures=max(0,int(w.get("failures",0)))
        reliability=max(0,1-failures/jobs)
        score=round(min(100,outcome_score*.75 + reliability*25),2)
        result=dict(w)
        result["verified_outcome_score"]=outcome_score
        result["verified_score"]=score
        result["verified_signals"]=relevant
        result["evaluated_at"]=now()
        # Permanent requires >=3 jobs AND real downstream evidence score.
        if jobs>=3 and outcome_score>=35 and score>=60:
            result["status"]="permanent"
        elif jobs>=5 and (outcome_score==0 or score<35):
            result["status"]="retired"
        else:
            result["status"]="probation"
        return result

    def run(self):
        registry_path=self.root/".companyos_runtime/continuous_improvement/registry.json"
        reg=readj(registry_path,{"workers":{},"cycles":0})
        signals=self.collect()
        workers=reg.get("workers",{})
        evaluated={}
        for key,w in workers.items():
            evaluated[key]=self.evaluate_worker(w,signals)
        reg["workers"]=evaluated
        reg["verified_outcome_policy"]=True
        reg["verified_outcome_updated_at"]=now()
        writej(registry_path,reg)
        report={
          "timestamp":now(),
          "signals":signals,
          "workers":evaluated,
          "permanent":[k for k,w in evaluated.items() if w.get("status")=="permanent"],
          "probation":[k for k,w in evaluated.items() if w.get("status")=="probation"],
          "retired":[k for k,w in evaluated.items() if w.get("status")=="retired"],
          "policy":{
            "file_presence_is_success":False,
            "revenue_requires_explicit_observed_marker":True,
            "permanence_requires_downstream_outcomes":True
          }
        }
        writej(self.rt/"latest.json",report)
        return report
