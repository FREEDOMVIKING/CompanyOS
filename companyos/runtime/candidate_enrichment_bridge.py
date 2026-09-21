from __future__ import annotations
import json,re,time,hashlib
from pathlib import Path
ROOT=Path.home()/"companyos"
RT=Path.home()/".companyos_runtime"
RESEARCH=RT/"canonical_research_outputs"
CANDIDATES=RT/"profit_first_candidates"
STATE=RT/"candidate_enrichment_bridge_state.json"
BAD=("research markets before building","research/analysis only","generate at least","for each candidate","use 0-100 numeric scores","mark estimates honestly","preserve all external","companyos opportunity engine test","this stage is research")
def load(p):
 try:return json.loads(p.read_text())
 except:return {}
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,indent=2,sort_keys=True,default=str)+"\n")
def pick(d,*ks,default=None):
 for k in ks:
  if d.get(k) not in (None,"",[],{}): return d[k]
 for nk in ("candidate","opportunity","business","analysis","market_analysis","economics","scores"):
  n=d.get(nk)
  if isinstance(n,dict):
   for k in ks:
    if n.get(k) not in (None,"",[],{}): return n[k]
 return default
def num(v,d=0):
 try:return float(v)
 except:return d
def prob(v):
 x=num(v,0)
 if 0<x<=1:x*=100
 return max(0,min(100,x))
def urls(x):
 out=[]
 def walk(v):
  if isinstance(v,dict):
   for z in v.values():walk(z)
  elif isinstance(v,list):
   for z in v:walk(z)
  elif isinstance(v,str):
   for u in re.findall(r'https?://[^\\s"\')\\]>]+',v):
    if u not in out:out.append(u)
 walk(x); return out[:20]
def semantics(d):
 ks={str(k).lower() for k in d}
 wanted=("customer","target_customer","buyer","market","problem","customer_problem","offer","service","product","business_model","revenue_model","mechanism")
 h=sum(k in ks for k in wanted)
 for nk in ("candidate","opportunity","business","market_analysis"):
  n=d.get(nk)
  if isinstance(n,dict):
   nks={str(k).lower() for k in n}; h+=sum(k in nks for k in wanted)
 return h
def normalize(d,p):
 if not isinstance(d,dict) or semantics(d)<2:return None
 t=json.dumps(d,default=str).lower()
 if any(x in t for x in BAD) and semantics(d)<3:return None
 name=str(pick(d,"name","opportunity_name","venture_name","business_name","title",default=p.stem))[:160]
 evidence=pick(d,"evidence","sources","citations","market_evidence",default=[])
 u=urls(d)
 ec=len(evidence) if isinstance(evidence,(list,dict)) else (1 if isinstance(evidence,str) and evidence.strip() else 0)
 ec=max(ec,len(u))
 action=str(pick(d,"next_action","recommended_action","execution_action","first_action","recommended_next_step",default="") or "").strip()
 if ec<1 or not action:return None
 return {
  "schema":"companyos.enriched_profit_candidate.v1","name":name,
  "business_model":pick(d,"business_model","model","revenue_model","mechanism",default="unknown"),
  "target_customer":pick(d,"target_customer","customer","buyer","customer_segment",default="unknown"),
  "problem":pick(d,"problem","customer_problem","pain_point",default="unknown"),
  "offer":pick(d,"offer","service","product","value_proposition",default="unknown"),
  "market":pick(d,"market","industry","sector","category",default="unknown"),
  "expected_profit":num(pick(d,"expected_profit","projected_profit","expected_net_profit","profit",default=0)),
  "margin":num(pick(d,"expected_margin_pct","margin_pct","profit_margin","margin",default=0)),
  "probability":prob(pick(d,"probability_success_pct","success_probability","probability","confidence",default=0)),
  "evidence_count":ec,"evidence_quality":prob(pick(d,"evidence_quality_pct","evidence_quality","evidence_confidence",default=0)),
  "readiness":prob(pick(d,"execution_readiness_pct","execution_readiness","readiness",default=0)),
  "time_to_cash_days":max(.1,num(pick(d,"time_to_cash_days","days_to_cash",default=30),30)),
  "capital_required":max(0,num(pick(d,"capital_required","startup_cost","required_capital","cost",default=0))),
  "next_action":action,"evidence":evidence or u,"source_urls":u,"source_research_artifact":str(p.relative_to(ROOT)),
  "enriched_at_unix":time.time()
 }
def refresh_enrichments(max_age_hours=72):
 CANDIDATES.mkdir(parents=True,exist_ok=True); cutoff=time.time()-max_age_hours*3600
 scanned=accepted=rejected=0; written=[]
 if RESEARCH.exists():
  for p in sorted(RESEARCH.rglob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
   if p.stat().st_mtime<cutoff:continue
   scanned+=1; row=normalize(load(p),p)
   if not row: rejected+=1; continue
   raw=json.dumps(row,sort_keys=True,default=str)
   fp=hashlib.sha256(raw.encode()).hexdigest()[:16]
   slug=re.sub(r'[^a-z0-9]+','_',row['name'].lower()).strip('_')[:72] or fp
   out=CANDIDATES/f"enriched_{slug}_{fp}.json"; save(out,row); written.append(str(out.relative_to(ROOT))); accepted+=1
   if accepted>=50:break
 st={"ts":time.time(),"scanned":scanned,"accepted":accepted,"rejected":rejected,"written":written}; save(STATE,st); return st
if __name__=="__main__":print(json.dumps(refresh_enrichments(),indent=2))
