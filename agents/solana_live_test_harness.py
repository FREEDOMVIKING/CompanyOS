#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
CFG=MEM/"phase33d_live_test_config.json"
REG=MEM/"treasury_wallet_registry.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def run_cmd(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:
        data=json.loads(p.stdout)
    except:
        data={"raw_stdout":p.stdout,"stderr":p.stderr}
    return p.returncode,data

def source_address():
    for w in load(REG,{}).get("wallets",[]):
        if w.get("chain")=="solana" and w.get("enabled"):
            return w.get("address")
    return None

def main():
    cfg=load(CFG,{})
    if len(sys.argv)<2:
        print(json.dumps({
          "success":True,
          "status":"phase33d_live_test_ready",
          "usage":"python companyos/solanalivetestctl live DESTINATION AMOUNT_SOL AMOUNT_USD",
          "max_test_amount_sol":cfg["max_test_amount_sol"],
          "max_test_amount_usd":cfg["max_test_amount_usd"]
        },indent=2))
        return 0

    if sys.argv[1]!="live":
        print(json.dumps({"success":False,"status":"explicit_live_flag_required"},indent=2))
        return 1

    if len(sys.argv)<5:
        print(json.dumps({"success":False,"status":"missing_arguments"},indent=2))
        return 1

    dest=sys.argv[2].strip()
    amount_sol=float(sys.argv[3])
    amount_usd=float(sys.argv[4])
    src=source_address()

    if not src:
        print(json.dumps({"success":False,"status":"registered_solana_source_missing"},indent=2))
        return 1

    if cfg.get("require_destination_not_source") and dest==src:
        print(json.dumps({"success":False,"status":"destination_must_differ_from_source"},indent=2))
        return 1

    if amount_sol<=0 or amount_sol>float(cfg["max_test_amount_sol"]):
        print(json.dumps({
          "success":False,
          "status":"test_amount_exceeds_sol_limit",
          "max_test_amount_sol":cfg["max_test_amount_sol"]
        },indent=2))
        return 1

    if amount_usd<=0 or amount_usd>float(cfg["max_test_amount_usd"]):
        print(json.dumps({
          "success":False,
          "status":"test_amount_exceeds_usd_limit",
          "max_test_amount_usd":cfg["max_test_amount_usd"]
        },indent=2))
        return 1

    # Create governed Phase 32 proposal.
    rc,proposal_result=run_cmd([
      sys.executable,"companyos/transactionproposalctl","propose",
      str(amount_usd),str(amount_sol),"SOL","solana",dest,
      "Phase 33D controlled live Solana transfer test"
    ])

    if rc!=0 or not proposal_result.get("success"):
        print(json.dumps({"success":False,"status":"proposal_creation_failed","detail":proposal_result},indent=2))
        return 1

    proposal=proposal_result.get("proposal") or {}
    pid=proposal.get("proposal_id")

    if proposal.get("status")!="ready_for_signing" or not proposal.get("signing_authorized"):
        print(json.dumps({
          "success":False,
          "status":"proposal_not_authorized",
          "proposal":proposal
        },indent=2))
        return 1

    # Execute through Phase 33A: balance check -> blockhash -> local signer
    # -> simulation/preflight -> broadcast -> confirmation.
    rc,exec_result=run_cmd([
      sys.executable,"companyos/solanaexecutionctl","execute",pid
    ])

    print(json.dumps({
      "success":rc==0 and bool(exec_result.get("success")),
      "status":"phase33d_live_test_complete",
      "proposal_id":pid,
      "execution":exec_result
    },indent=2))

    return 0 if rc==0 and exec_result.get("success") else 1

if __name__=="__main__":
    raise SystemExit(main())
