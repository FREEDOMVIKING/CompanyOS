from __future__ import annotations
import hashlib,json,math,os,time
from dataclasses import asdict,dataclass,field
from pathlib import Path
from typing import Any
ROOT=Path.home()/"companyos"; RT=ROOT/".companyos_runtime"; STORE=RT/"profit_opportunities"
LEDGER=RT/"profit_opportunity_ledger.jsonl"; STATUS=RT/"profit_opportunity_status.json"
EXECUTION_STATE=RT/"profit_execution_state.json"
EXECUTION_COOLDOWN_SECONDS=int(os.getenv("COMPANYOS_EXECUTION_REDISPATCH_SECONDS","1800"))
POLICY=("must not","research only","candidate json must","generate at least","for each candidate","use 0-100","this stage is research")
HINTS=("sell","service","broker","agency","arbitrage","resell","license","affiliate","contract","acquire","marketplace","software","automation","data","lead","consult","rent","subscription","commission","build","launch")
def num(v,d=0):
 try:return float(v)
 except:return d
def clamp(v):return max(0,min(100,num(v)))
def pick(d,*ks,default=None):
 for k in ks:
  if d.get(k) not in (None,""):return d[k]
 for n in ("opportunity","candidate","economics","scores","analysis","market_analysis"):
  x=d.get(n)
  if isinstance(x,dict):
   for k in ks:
    if x.get(k) not in (None,""):return x[k]
 return default
def text(x):return json.dumps(x,sort_keys=True,default=str).lower()
def event(kind,**kw):
 LEDGER.parent.mkdir(parents=True,exist_ok=True)
 with LEDGER.open("a") as f:f.write(json.dumps({"ts":time.time(),"kind":kind,**kw},sort_keys=True,default=str)+"\n")
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,indent=2,sort_keys=True,default=str))
@dataclass
class Opportunity:
 id:str; name:str; source:str; mechanism:str="unknown"; category:str="unknown"; next_action:str=""
 expected_profit:float=0; margin:float=0; time_to_cash_days:float=30; capital_required:float=0; capital_at_risk:float=0
 probability:float=0; evidence_count:int=0; evidence_quality:float=0; scalability:float=50; reversibility:float=70
 readiness:float=0; complexity:float=50; compliance_risk:float=10; dependency_risk:float=30; score:float=0
 payload:dict[str,Any]=field(default_factory=dict)
def normalize(d,p):
 if not isinstance(d,dict):return None
 t=text(d); stem=p.stem.lower()
 if any(x in stem for x in ("do_not_","must_","generate_at_least","for_each_","use_0_100","this_stage_is_research")):return None
 name=str(pick(d,"name","title","opportunity_name","venture_name","action",default=p.stem))
 action=str(pick(d,"next_action","recommended_action","first_action","execution_action",default=""))
 has_action=bool(action) or any(h in t for h in HINTS)
 if any(x in t for x in POLICY) and not has_action:return None
 profit=num(pick(d,"expected_profit","projected_profit","profit","expected_net_profit",default=0))
 margin=num(pick(d,"expected_margin_pct","margin_pct","margin","profit_margin",default=0))
 if not has_action and profit<=0 and margin<=0:return None
 ev=pick(d,"evidence","evidence_sources","sources",default=[])
 eid=hashlib.sha256((name+"|"+str(p)).encode()).hexdigest()[:24]
 return Opportunity(eid,name,str(p),str(pick(d,"profit_mechanism","mechanism","revenue_mechanism","model","business_model",default="unknown")),
  str(pick(d,"category","sector","market","industry","type",default="unknown")),action,profit,margin,max(.1,num(pick(d,"time_to_cash_days","days_to_cash",default=30),30)),
  max(0,num(pick(d,"capital_required","startup_cost","required_capital","cost",default=0))),max(0,num(pick(d,"capital_at_risk","downside","max_loss",default=0))),
  clamp(pick(d,"probability_success_pct","success_probability","confidence",default=0)),int(num(pick(d,"evidence_count",default=len(ev) if isinstance(ev,list) else 0))),
  clamp(pick(d,"evidence_quality_pct","evidence_quality","evidence_confidence",default=0)),clamp(pick(d,"scalability_pct","scalability","scale_score",default=50)),
  clamp(pick(d,"reversibility_pct","reversibility",default=70)),clamp(pick(d,"execution_readiness_pct","execution_readiness","readiness",default=50 if has_action else 0)),
  clamp(pick(d,"complexity_pct","complexity",default=50)),clamp(pick(d,"legal_compliance_risk_pct","compliance_risk","legal_risk",default=10)),
  clamp(pick(d,"external_dependency_pct","external_dependency","dependency_risk",default=30)),payload=d)
def score(o):
 p=o.probability/100; ev=max(0,o.expected_profit)*p-max(0,o.capital_at_risk)*(1-p)
 evn=100*(1-math.exp(-max(0,ev)/5000)); speed=100/(1+o.time_to_cash_days/14)
 eff=100 if o.capital_required<=0 and o.expected_profit>0 else 100*(1-math.exp(-max(0,o.expected_profit)/(max(1,o.capital_required)*2)))
 up=.30*evn+.10*clamp(o.margin)+.12*speed+.10*eff+.12*o.evidence_quality+.10*o.readiness+.09*o.scalability+.07*o.reversibility
 down=.08*o.complexity+.12*o.compliance_risk+.07*o.dependency_risk
 o.score=round(clamp(up-down),2);return o
def paths():
 roots=[RT/"profit_first_candidates",RT/"profit_opportunities",ROOT/"workspace",ROOT/"generated_products",ROOT/"generated_companies"]
 seen=set()
 for r in roots:
  if r.exists():
   for p in r.rglob("*.json"):
    if p not in seen and p not in (STATUS,):seen.add(p);yield p
def discover():
 out=[]
 for p in paths():
  try:o=normalize(json.loads(p.read_text()),p)
  except:continue
  if o:out.append(score(o))
 best={}
 for o in out:
  k=(o.name.lower(),o.mechanism.lower())
  if k not in best or o.score>best[k].score:best[k]=o
 out=sorted(best.values(),key=lambda o:(o.score,o.expected_profit),reverse=True);event("DISCOVER",count=len(out));return out
def choose():
 rows=discover(); eligible=[]
 for o in rows:
  reasons=[]
  if o.score<num(os.getenv("COMPANYOS_PROFIT_MIN_SCORE","45")):reasons.append("score")
  if o.probability<20 and o.evidence_count<1:reasons.append("evidence")
  if o.compliance_risk>=80:reasons.append("compliance")
  if not o.next_action:reasons.append("next_action")
  if not reasons:eligible.append(o)
 chosen=eligible[0] if eligible else None
 x={"ts":time.time(),"objective":"risk_adjusted_realized_profit","candidate_count":len(rows),"eligible_count":len(eligible),
    "decision":"execute_candidate" if chosen else "research_more","chosen":asdict(chosen) if chosen else None,
    "ranked":[asdict(o) for o in rows[:30]]}
 write(STATUS,x);event("DECISION",decision=x["decision"]);return x
def _exec_load():
 try:return json.loads(EXECUTION_STATE.read_text())
 except:return {}

def _exec_save(x):write(EXECUTION_STATE,x)

def _slug(v):
 import re
 return (re.sub(r"[^a-z0-9]+","-",str(v).lower()).strip("-") or "opportunity")[:72]

def _start_execution(o):
 from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
 slug=_slug(o.get("name") or o.get("id"))
 venture=ROOT/"workspace"/slug
 venture.mkdir(parents=True,exist_ok=True)
 write(venture/"venture_brief.json",{
  "canonical_id":slug,"name":o.get("name"),"stage":"EXECUTE",
  "objective":"realized_profit","opportunity":o,"updated_at_unix":time.time(),
  "next_required_outcome":"Produce measurable progress toward a sellable offer, deployment, customer acquisition, or revenue evidence."
 })
 goal=(
  f"Advance venture '{slug}' into concrete execution.\n"
  f"Selected opportunity: {o.get('name')}\n"
  f"Score: {o.get('score')}\n"
  f"Expected profit: {o.get('expected_profit')}\n"
  f"Recommended next action: {o.get('next_action')}\n\n"
  "Do not return to broad research unless a specific missing fact blocks execution.\n"
  "Build the smallest sellable offer/product/service supported by evidence.\n"
  "Create price, buyer definition, acceptance criteria, customer-facing asset, and execution checklist.\n"
  "Build/test the smallest viable version if build work is required.\n"
  "Use configured deployment/outreach connectors only when existing policy authorizes them.\n"
  f"Persist measurable stage/evidence updates in workspace/{slug}.\n"
  "Prefer a path to first cash over more documentation.\n"
  "Never bypass wallet, finance, credential, approval, signer, reconciliation, legal, destructive-action, or irreversible-action gates.\n"
  "Do not initiate a financial transaction merely to prove activity.\n"
 )
 rec=AutonomousCEOOrchestrator().start(goal=goal,max_cycles=220,max_follow_up_depth=8,priority_base=360)
 oid=getattr(rec,"orchestration_id",None)
 st=_exec_load(); now=time.time()
 st["last_opportunity_id"]=o.get("id"); st["last_dispatch_unix"]=now; st["last_orchestration_id"]=oid
 st.setdefault("dispatches",[]).append({"ts":now,"name":o.get("name"),"slug":slug,"orchestration_id":oid})
 st["dispatches"]=st["dispatches"][-200:]; _exec_save(st)
 return {"started":True,"workspace":str(venture),"canonical_id":slug,"orchestration_id":oid}

def dispatch():
 x=choose()
 if not x["chosen"]:
  y={"ok":True,"action":"research_more","reason":"no_execution_qualified_profit_opportunity"}
  write(RT/"profit_opportunity_dispatch.json",y); return y
 o=x["chosen"]; STORE.mkdir(parents=True,exist_ok=True)
 selected=STORE/("selected_"+o["id"]+".json")
 write(selected,{"schema":"companyos.profit_opportunity.v2","stage":"EXECUTE","objective":"realized_profit","opportunity":o,
  "constraints":{"connector_gates":True,"financial_gates":True,"credential_gates":True,"irreversible_action_gates":True}})
 st=_exec_load(); since=time.time()-float(st.get("last_dispatch_unix",0) or 0)
 if st.get("last_opportunity_id")==o.get("id") and since<EXECUTION_COOLDOWN_SECONDS:
  y={"ok":True,"action":"continue_existing_execution","name":o["name"],"score":o["score"],
     "orchestration_id":st.get("last_orchestration_id"),"seconds_until_redispatch":round(EXECUTION_COOLDOWN_SECONDS-since,1)}
  write(RT/"profit_opportunity_dispatch.json",y); event("EXECUTION_CONTINUE",name=o["name"],score=o["score"]); return y
 try:
  ex=_start_execution(o)
  y={"ok":True,"action":"execution_orchestration_started","selected_path":str(selected),"name":o["name"],"score":o["score"],
     "next_action":o["next_action"],**ex}
  write(RT/"profit_opportunity_dispatch.json",y); event("EXECUTION_STARTED",name=o["name"],score=o["score"],orchestration_id=ex.get("orchestration_id")); return y
 except Exception as exc:
  y={"ok":False,"action":"execution_start_failed","name":o["name"],"score":o["score"],"error":f"{type(exc).__name__}: {exc}"}
  write(RT/"profit_opportunity_dispatch.json",y); event("EXECUTION_START_FAILED",name=o["name"],error=y["error"]); return y

def main():
 import argparse
 a=argparse.ArgumentParser();a.add_argument("command",choices=("discover","choose","dispatch","status"));q=a.parse_args().command
 r=[asdict(x) for x in discover()] if q=="discover" else choose() if q=="choose" else dispatch() if q=="dispatch" else {"status":json.loads(STATUS.read_text()) if STATUS.exists() else {}}
 print(json.dumps(r,indent=2,sort_keys=True,default=str))
if __name__=="__main__":main()



# COMPANYOS_CANDIDATE_INTELLIGENCE_V2

_CI_INTERNAL_MARKERS = (
    "companyos opportunity engine test",
    "research markets before building",
    "research/analysis only",
    "preserve all external",
    "mark estimates honestly",
    "discover at least",
    "materially different opportunities",
    "persist a market-scan",
    "persist a market scan",
    "do not generate superficial",
    "do not duplicate",
    "construction and service businesses may appear",
    "prefer commercially distinct opportunities",
    "for each candidate",
    "each record must",
    "generate at least",
    "use 0-100 numeric scores",
    "this stage is research",
)

def _ci_text_from_opportunity(o):
    parts = [
        str(getattr(o, "name", "") or ""),
        str(getattr(o, "source", "") or ""),
        str(getattr(o, "next_action", "") or ""),
    ]
    payload = getattr(o, "payload", {}) or {}
    try:
        parts.append(json.dumps(payload, sort_keys=True, default=str))
    except Exception:
        parts.append(str(payload))
    return " ".join(parts).lower()

def candidate_is_internal_instruction(o):
    t = _ci_text_from_opportunity(o)
    source = str(getattr(o, "source", "") or "").lower()
    name = str(getattr(o, "name", "") or "").lower()
    if any(x in t for x in _CI_INTERNAL_MARKERS):
        return True
    if "/tests/" in source or source.startswith("tests/"):
        return True
    if "test" in name and "opportunity" in name:
        return True
    imperative_hits = sum(
        1 for x in (
            "must ", "do not ", "preserve ", "generate at least",
            "for each candidate", "research markets", "use 0-100"
        ) if x in t
    )
    if imperative_hits >= 2 and not getattr(o, "next_action", ""):
        return True
    return False

_candidate_intel_legacy_discover = discover

def discover():
    rows = _candidate_intel_legacy_discover()
    commercial = [o for o in rows if not candidate_is_internal_instruction(o)]
    event(
        "CANDIDATE_INTELLIGENCE_FILTER",
        input_count=len(rows),
        commercial_count=len(commercial),
        rejected_internal_count=len(rows)-len(commercial),
    )
    return commercial

def _candidate_qualification_reasons(o):
    reasons = []
    min_score = num(os.getenv("COMPANYOS_PROFIT_MIN_SCORE", "45"))
    if o.score < min_score:
        reasons.append("score_below_execution_threshold")
    if o.evidence_count < 1:
        reasons.append("missing_external_evidence")
    if o.probability <= 0:
        reasons.append("probability_unestimated")
    if o.expected_profit <= 0:
        reasons.append("profit_unestimated")
    if o.readiness <= 0:
        reasons.append("readiness_unestimated")
    if not str(o.next_action or "").strip():
        reasons.append("missing_executable_next_action")
    if o.compliance_risk >= 80:
        reasons.append("compliance_risk_too_high")
    return reasons

def _write_candidate_enrichment_queue(rows):
    queue = []
    for o in rows[:30]:
        reasons = _candidate_qualification_reasons(o)
        if not reasons:
            continue
        queue.append({
            "id": o.id,
            "name": o.name,
            "source": o.source,
            "score": o.score,
            "missing_or_blocking": reasons,
            "current": {
                "expected_profit": o.expected_profit,
                "probability": o.probability,
                "evidence_count": o.evidence_count,
                "evidence_quality": o.evidence_quality,
                "readiness": o.readiness,
                "time_to_cash_days": o.time_to_cash_days,
                "capital_required": o.capital_required,
                "next_action": o.next_action,
            },
            "research_contract": (
                "Research only this commercial opportunity. Resolve the listed gaps "
                "with real evidence. Do not invent probability, profit, readiness, "
                "customers, or evidence. Return evidence sources and one executable next action."
            ),
        })
    write(RT / "profit_candidate_enrichment_queue.json", {
        "ts": time.time(),
        "count": len(queue),
        "candidates": queue,
    })
    return queue

def choose():
    rows = discover()
    eligible = []
    rejected = []
    for o in rows:
        reasons = _candidate_qualification_reasons(o)
        if reasons:
            rejected.append({
                "id": o.id,
                "name": o.name,
                "source": o.source,
                "score": o.score,
                "reasons": reasons,
            })
        else:
            eligible.append(o)
    chosen = eligible[0] if eligible else None
    queue = _write_candidate_enrichment_queue(rows)
    x = {
        "ts": time.time(),
        "objective": "risk_adjusted_realized_profit",
        "candidate_count": len(rows),
        "eligible_count": len(eligible),
        "rejected_count": len(rejected),
        "decision": "execute_candidate" if chosen else "research_more",
        "chosen": asdict(chosen) if chosen else None,
        "ranked": [asdict(o) for o in rows[:30]],
        "qualification_rejections": rejected[:30],
        "enrichment_queue_count": len(queue),
    }
    write(STATUS, x)
    event(
        "DECISION",
        decision=x["decision"],
        candidate_count=len(rows),
        eligible_count=len(eligible),
        enrichment_queue_count=len(queue),
    )
    return x
