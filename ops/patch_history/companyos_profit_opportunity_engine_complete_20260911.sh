#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"
BRANCH="companyos-continuous-fix-2026-09-11"
cd "$ROOT"
[ "$(git branch --show-current)" = "$BRANCH" ] || { echo "ERROR wrong branch"; exit 2; }
mkdir -p companyos/runtime scripts .companyos_runtime/profit_opportunities
cat > companyos/runtime/profit_opportunity_engine.py <<'PYFILE'
from __future__ import annotations
import hashlib,json,math,os,time
from dataclasses import asdict,dataclass,field
from pathlib import Path
from typing import Any
ROOT=Path.home()/"companyos"; RT=ROOT/".companyos_runtime"; STORE=RT/"profit_opportunities"
LEDGER=RT/"profit_opportunity_ledger.jsonl"; STATUS=RT/"profit_opportunity_status.json"
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
def dispatch():
 x=choose()
 if not x["chosen"]:
  y={"ok":True,"action":"research_more","reason":"no_execution_qualified_profit_opportunity"};write(RT/"profit_opportunity_dispatch.json",y);return y
 o=x["chosen"]; STORE.mkdir(parents=True,exist_ok=True)
 rec={"schema":"companyos.profit_opportunity.v1","stage":"EXECUTE","objective":"realized_profit","opportunity":o,
      "constraints":{"connector_gates":True,"financial_gates":True,"credential_gates":True,"irreversible_action_gates":True}}
 p=STORE/("selected_"+o["id"]+".json");write(p,rec)
 y={"ok":True,"action":"execute_candidate","selected_path":str(p),"name":o["name"],"score":o["score"],"next_action":o["next_action"]}
 write(RT/"profit_opportunity_dispatch.json",y);event("EXECUTE_SELECTED",name=o["name"],score=o["score"]);return y
def main():
 import argparse
 a=argparse.ArgumentParser();a.add_argument("command",choices=("discover","choose","dispatch","status"));q=a.parse_args().command
 r=[asdict(x) for x in discover()] if q=="discover" else choose() if q=="choose" else dispatch() if q=="dispatch" else {"status":json.loads(STATUS.read_text()) if STATUS.exists() else {}}
 print(json.dumps(r,indent=2,sort_keys=True,default=str))
if __name__=="__main__":main()

PYFILE
cat > companyos/runtime/profit_opportunity_runtime.py <<'PYFILE'
from __future__ import annotations
import json,os,time
from pathlib import Path
from companyos.runtime.profit_opportunity_engine import dispatch
RT=Path.home()/"companyos/.companyos_runtime"; STATE=RT/"profit_opportunity_runtime_state.json"
def run():
 interval=max(60,int(os.getenv("COMPANYOS_PROFIT_ENGINE_INTERVAL_SECONDS","300")))
 while not (RT/"STOP_CONTINUOUS").exists():
  try:x={"running":True,"healthy":True,"last_cycle_unix":time.time(),"result":dispatch()}
  except Exception as e:x={"running":True,"healthy":False,"last_cycle_unix":time.time(),"error":repr(e)}
  STATE.write_text(json.dumps(x,indent=2,sort_keys=True,default=str));time.sleep(interval)
if __name__=="__main__":run()

PYFILE
cat > scripts/validate_profit_opportunity_engine.py <<'PYFILE'
import json,tempfile
from pathlib import Path
from companyos.runtime import profit_opportunity_engine as e
d={"name":"Commissioned infrastructure sourcing","profit_mechanism":"commission","next_action":"verify suppliers and a qualified buyer","expected_profit":12000,"expected_margin_pct":82,"time_to_cash_days":21,"capital_required":250,"capital_at_risk":250,"probability_success_pct":58,"evidence_count":4,"evidence_quality_pct":72,"scalability_pct":68,"reversibility_pct":95,"execution_readiness_pct":75,"complexity_pct":35,"legal_compliance_risk_pct":15}
with tempfile.TemporaryDirectory() as z:
 p=Path(z)/"x.json";p.write_text(json.dumps(d));o=e.normalize(d,p);assert o and e.score(o).score>0
bad={"name":"Use 0-100 numeric scores","instruction":"for each candidate use 0-100 numeric scores"}
with tempfile.TemporaryDirectory() as z:
 p=Path(z)/"use_0_100.json";assert e.normalize(bad,p) is None
print("COMPANYOS_PROFIT_OPPORTUNITY_ENGINE_VALIDATION=PASS")

PYFILE

cat > scripts/companyos_profitctl <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/companyos"
exec python -m companyos.runtime.profit_opportunity_engine "$@"
SH
chmod +x scripts/companyos_profitctl

python -m py_compile companyos/runtime/profit_opportunity_engine.py companyos/runtime/profit_opportunity_runtime.py scripts/validate_profit_opportunity_engine.py
python scripts/validate_profit_opportunity_engine.py

echo "===== PROFIT DISCOVERY ====="
scripts/companyos_profitctl discover
echo "===== PROFIT DECISION ====="
scripts/companyos_profitctl choose
echo "===== PROFIT DISPATCH ====="
scripts/companyos_profitctl dispatch

git add companyos/runtime/profit_opportunity_engine.py companyos/runtime/profit_opportunity_runtime.py scripts/validate_profit_opportunity_engine.py scripts/companyos_profitctl
git commit -m "Add business-model-agnostic profit opportunity engine" || true
git push origin "$BRANCH"

# Run the profit engine continuously without disrupting the already-healthy supervisor.
mkdir -p .companyos_runtime
if [ -f .companyos_runtime/profit_engine.pid ]; then
  old="$(cat .companyos_runtime/profit_engine.pid 2>/dev/null || true)"
  [ -z "$old" ] || kill "$old" 2>/dev/null || true
fi
nohup python -m companyos.runtime.profit_opportunity_runtime >> .companyos_runtime/profit_opportunity_runtime.log 2>&1 &
echo $! > .companyos_runtime/profit_engine.pid
sleep 3

echo "===== EXISTING COMPANYOS HEALTH ====="
scripts/companyosctl health || true
echo "===== PROFIT ENGINE PROCESS ====="
ps -p "$(cat .companyos_runtime/profit_engine.pid)" -o pid=,etime=,cmd= || true
echo "===== PROFIT ENGINE STATUS ====="
scripts/companyos_profitctl status
echo "COMPANYOS_PROFIT_OPPORTUNITY_ENGINE_COMPLETE=PASS"
