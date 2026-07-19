#!/usr/bin/env python3
import json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"phase34_autonomous_treasury_config.json"
PROPOSALS=MEM/"transaction_proposals.json"
DESTS=MEM/"treasury_destination_registry.json"
STATE=MEM/"phase34_autonomous_treasury_state.json"
REPORT=MEM/"phase34_autonomous_treasury_report.json"
AUDIT=MEM/"phase34_autonomous_treasury_audit.jsonl"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def audit(x):
    with AUDIT.open("a") as f:f.write(json.dumps({"at":now(),**x})+"\n")

def destination_allowed(chain,address):
    for x in load(DESTS,{"destinations":[]}).get("destinations",[]):
        if x.get("enabled") and x.get("chain")==chain and x.get("address")==address:
            return True
    return False

def execute_sol(pid):
    p=subprocess.run(
      [sys.executable,"companyos/solanaexecutionctl","execute",pid],
      cwd=ROOT,text=True,capture_output=True,timeout=300
    )
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_executor_output","stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def run():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"autonomous_treasury_disabled","executed_count":0}
    if cfg.get("kill_switch"):
        return {"success":True,"status":"autonomous_treasury_kill_switch_active","executed_count":0}

    q=load(PROPOSALS,{"proposals":[]})
    ready=[
      x for x in q.get("proposals",[])
      if x.get("status")=="ready_for_signing"
      and x.get("signing_authorized")
      and not x.get("broadcast_authorized")
    ]

    maxn=int(cfg.get("max_transactions_per_cycle",5))
    results=[]
    failures=0

    for x in ready[:maxn]:
        pid=x.get("proposal_id");chain=x.get("chain");asset=x.get("asset");dest=x.get("destination")

        if cfg.get("require_registered_destination") and not destination_allowed(chain,dest):
            row={"proposal_id":pid,"success":False,"status":"destination_not_registered","destination":dest}
            results.append(row);audit(row);continue

        allowed_assets=(cfg.get("supported_live_routes",{}).get(chain) or [])
        if asset not in allowed_assets:
            row={"proposal_id":pid,"success":False,"status":"live_route_not_enabled","chain":chain,"asset":asset}
            results.append(row);audit(row);continue

        if chain=="solana" and asset=="SOL":
            rc,r=execute_sol(pid)
        else:
            rc,r=1,{"success":False,"status":"executor_not_implemented"}

        row={"proposal_id":pid,"success":rc==0 and bool(r.get("success")),"execution":r}
        results.append(row);audit(row)

        if not row["success"]:
            failures+=1
            if cfg.get("stop_on_first_execution_failure"):break

        time.sleep(int(cfg.get("minimum_seconds_between_broadcasts",10)))

    report={
      "generated_at":now(),
      "ready_count":len(ready),
      "executed_count":sum(1 for x in results if x.get("success")),
      "failure_count":failures,
      "results":results
    }
    save(REPORT,report)
    save(STATE,{
      "last_run_at":now(),
      "failure_count":failures,
      "last_executed_count":report["executed_count"],
      "kill_switch":cfg.get("kill_switch",False)
    })
    return {"success":failures==0,"status":"autonomous_treasury_cycle_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "run"
if a=="status":
    r={
      "success":True,
      "status":"autonomous_treasury_status",
      "config":load(CFG,{}),
      "state":load(STATE,{})
    }
else:
    r=run()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
