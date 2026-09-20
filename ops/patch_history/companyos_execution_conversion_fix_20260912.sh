#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd ~/companyos
source ~/.companyos_launch_env
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p ".companyos_backups/execution_conversion_$STAMP"
cp companyos/runtime/profit_opportunity_engine.py ".companyos_backups/execution_conversion_$STAMP/"

python - <<'PY'

from pathlib import Path
import re

p=Path("companyos/runtime/profit_opportunity_engine.py")
s=p.read_text()

if 'EXECUTION_STATE=RT/"profit_execution_state.json"' not in s:
    anchor='LEDGER=RT/"profit_opportunity_ledger.jsonl"; STATUS=RT/"profit_opportunity_status.json"\n'
    if anchor not in s:
        raise SystemExit("profit engine anchor not found")
    s=s.replace(
        anchor,
        anchor+'EXECUTION_STATE=RT/"profit_execution_state.json"\n'
               'EXECUTION_COOLDOWN_SECONDS=int(os.getenv("COMPANYOS_EXECUTION_REDISPATCH_SECONDS","1800"))\n',
        1
    )

m=re.search(r'(?m)^def\s+dispatch\s*\(\s*\)\s*:\s*\n',s)
if not m: raise SystemExit("dispatch() not found")
n=re.search(r'(?m)^def\s+main\s*\(',s[m.end():])
if not n: raise SystemExit("main() boundary not found")
start=m.start(); end=m.end()+n.start()

block = """def _exec_load():
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
  f"Advance venture '{slug}' into concrete execution.\\n"
  f"Selected opportunity: {o.get('name')}\\n"
  f"Score: {o.get('score')}\\n"
  f"Expected profit: {o.get('expected_profit')}\\n"
  f"Recommended next action: {o.get('next_action')}\\n\\n"
  "Do not return to broad research unless a specific missing fact blocks execution.\\n"
  "Build the smallest sellable offer/product/service supported by evidence.\\n"
  "Create price, buyer definition, acceptance criteria, customer-facing asset, and execution checklist.\\n"
  "Build/test the smallest viable version if build work is required.\\n"
  "Use configured deployment/outreach connectors only when existing policy authorizes them.\\n"
  f"Persist measurable stage/evidence updates in workspace/{slug}.\\n"
  "Prefer a path to first cash over more documentation.\\n"
  "Never bypass wallet, finance, credential, approval, signer, reconciliation, legal, destructive-action, or irreversible-action gates.\\n"
  "Do not initiate a financial transaction merely to prove activity.\\n"
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

"""

s=s[:start]+block+s[end:]
p.write_text(s)
print("EXECUTION_BRIDGE_PATCHED=YES")

PY

python -m py_compile companyos/runtime/profit_opportunity_engine.py
python -m unittest tests.test_self_evolution_guard

python - <<'PY'
import json
from companyos.runtime.profit_opportunity_engine import choose
x=choose()
print(json.dumps({
 "candidate_count":x.get("candidate_count"),
 "eligible_count":x.get("eligible_count"),
 "decision":x.get("decision"),
 "chosen":(x.get("chosen") or {}).get("name")
},indent=2))
PY

git add companyos/runtime/profit_opportunity_engine.py
git diff --cached --quiet || git commit -m "Convert selected profit opportunities into execution"
BRANCH="$(git branch --show-current)"
[ -n "$BRANCH" ] && git push origin "$BRANCH" || true

scripts/companyosctl restart || true
sleep 8

python - <<'PY'
import json
from companyos.runtime.profit_opportunity_engine import dispatch
print(json.dumps(dispatch(),indent=2,sort_keys=True,default=str))
PY

echo
echo "===== EXECUTION STATE ====="
cat .companyos_runtime/profit_execution_state.json 2>/dev/null || true
echo
echo "===== DISPATCH ====="
cat .companyos_runtime/profit_opportunity_dispatch.json 2>/dev/null || true
echo
echo "===== STATUS ====="
scripts/companyosctl status || true
echo
echo "COMPANYOS_EXECUTION_CONVERSION_FIX=PASS"
