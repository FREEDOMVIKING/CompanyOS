#!/usr/bin/env python3
import json, hashlib, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase37_safety_config.json"
PROPS=MEM/"transaction_proposals.json"
DESTS=MEM/"treasury_destination_registry.json"
IDEMP=MEM/"phase37_idempotency_registry.json"
REPORT=MEM/"phase37_safety_report.json"
AUDIT=MEM/"phase37_safety_audit.jsonl"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def audit(row):
    with AUDIT.open("a") as f:
        f.write(json.dumps({"at":now(), **row})+"\n")

def destination_allowed(chain,address):
    for x in load(DESTS,{"destinations":[]}).get("destinations",[]):
        if x.get("enabled") and x.get("chain")==chain and x.get("address")==address:
            return True
    return False

def idem_key(p):
    seed="|".join([
        str(p.get("proposal_id","")),
        str(p.get("chain","")),
        str(p.get("asset","")),
        str(p.get("source","")),
        str(p.get("destination","")),
        str(p.get("amount_native","")),
        str(p.get("amount_usd",""))
    ])
    return hashlib.sha256(seed.encode()).hexdigest()

def run_cmd(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def verify_proposal(p,cfg,idem):
    reasons=[]
    chain=p.get("chain")
    asset=p.get("asset")
    dest=p.get("destination")

    if p.get("status")!="ready_for_signing" or not p.get("signing_authorized"):
        reasons.append("not_phase32_authorized")

    if asset not in cfg.get("supported_routes",{}).get(chain,[]):
        reasons.append("unsupported_route")

    if cfg.get("require_registered_destination") and not destination_allowed(chain,dest):
        reasons.append("destination_not_registered")

    try:
        if float(p.get("amount_usd",0)) > float(cfg["single_transaction_auto_limit_usd"]):
            reasons.append("single_limit_exceeded")
    except:
        reasons.append("invalid_amount_usd")

    key=idem_key(p)
    if key in set(idem.get("executed",[])):
        reasons.append("duplicate_already_executed")
    if key in set(idem.get("reserved",[])):
        reasons.append("duplicate_already_reserved")

    return reasons,key

def dry_verify_route(p):
    chain=p.get("chain")
    asset=p.get("asset")

    if chain=="solana" and asset=="SOL":
        rc,r=run_cmd([sys.executable,"companyos/solanasignervalidationctl"])
        return rc,r

    if chain in ("evm","bitcoin"):
        rc,r=run_cmd([sys.executable,"companyos/phase36bdrysignctl"])
        return rc,r

    if chain=="solana" and asset in ("USDT-SPL","USDC-SPL"):
        # Route installation + signer readiness + monitored balances only.
        # No broadcast and no raw signed transaction persistence in Phase 37 verification mode.
        rc,r=run_cmd([sys.executable,"companyos/multichainexecutionctl","status"])
        if rc==0 and r.get("success"):
            return 0,{"success":True,"status":"spl_route_readiness_verified_no_broadcast"}
        return rc,r

    return 1,{"success":False,"status":"unsupported_route"}

def cycle():
    cfg=load(CFG,{})
    idem=load(IDEMP,{"executed":[],"reserved":[]})

    if not cfg.get("enabled"):
        return {"success":True,"status":"phase37_disabled"}

    proposals=[
        p for p in load(PROPS,{"proposals":[]}).get("proposals",[])
        if p.get("status")=="ready_for_signing" and p.get("signing_authorized")
    ]

    results=[]
    failures=0

    for p in proposals[:int(cfg.get("max_requests_per_cycle",10))]:
        reasons,key=verify_proposal(p,cfg,idem)

        if reasons:
            row={
              "proposal_id":p.get("proposal_id"),
              "success":False,
              "status":"safety_gate_blocked",
              "reasons":reasons,
              "idempotency_key":key
            }
            results.append(row)
            audit(row)
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break
            continue

        idem.setdefault("reserved",[]).append(key)
        save(IDEMP,idem)

        rc,dry=dry_verify_route(p)

        row={
          "proposal_id":p.get("proposal_id"),
          "success":rc==0 and bool(dry.get("success")),
          "status":"verified_no_broadcast" if rc==0 and dry.get("success") else "dry_verification_failed",
          "idempotency_key":key,
          "dry_verification":dry,
          "broadcast_attempted":False
        }

        results.append(row)
        audit(row)

        # Release reservation because Phase 37 is verification-only.
        idem=load(IDEMP,{"executed":[],"reserved":[]})
        idem["reserved"]=[x for x in idem.get("reserved",[]) if x!=key]
        save(IDEMP,idem)

        if not row["success"]:
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break

    report={
      "generated_at":now(),
      "broadcast_enabled":cfg.get("broadcast_enabled",False),
      "broadcast_attempted":False,
      "proposal_count":len(proposals),
      "result_count":len(results),
      "failure_count":failures,
      "results":results
    }
    save(REPORT,report)

    return {
      "success":failures==0,
      "status":"phase37_safety_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase37_safety_status",
      "config":load(CFG,{}),
      "idempotency":load(IDEMP,{"executed":[],"reserved":[]}),
      "last_report":load(REPORT,{})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
