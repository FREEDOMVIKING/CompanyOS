#!/usr/bin/env python3
import json, os, subprocess, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
REG=MEM/"treasury_wallet_registry.json"
OUT=MEM/"solana_signer_validation_report.json"
HEALTH=MEM/"solana_signer_validation_health.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:
        return json.loads(p.read_text())
    except:
        return d

def rpc(url,method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as r:
        j=json.loads(r.read().decode())
    if j.get("error"):
        raise RuntimeError(j["error"])
    return j.get("result")

def main():
    rpc_url=os.getenv("SOLANA_RPC_URL","").strip()
    signer_cmd=os.getenv("SOLANA_SIGNER_COMMAND","").strip()

    wallets=[w for w in load(REG,{}).get("wallets",[]) if w.get("chain")=="solana" and w.get("enabled")]
    source=wallets[0]["address"] if wallets else None

    report={
        "generated_at":now(),
        "rpc_configured":bool(rpc_url),
        "signer_configured":bool(signer_cmd),
        "registered_source":source,
        "checks":{}
    }

    if not rpc_url or not signer_cmd or not source:
        report["success"]=False
        report["status"]="missing_configuration"
        OUT.write_text(json.dumps(report,indent=2))
        HEALTH.write_text(json.dumps({"healthy":False,"last_checked_at":now()},indent=2))
        print(json.dumps(report,indent=2))
        raise SystemExit(1)

    bal=rpc(rpc_url,"getBalance",[source,{"commitment":"confirmed"}])
    report["checks"]["live_balance_lamports"]=(bal or {}).get("value",0)

    latest=rpc(rpc_url,"getLatestBlockhash",[{"commitment":"confirmed"}])
    blockhash=(latest or {}).get("value",{}).get("blockhash")
    report["checks"]["recent_blockhash_available"]=bool(blockhash)

    payload={
        "action":"build_and_sign_sol_transfer",
        "proposal_id":"phase33c-dry-validation",
        "source":source,
        "destination":source,
        "lamports":1,
        "recent_blockhash":blockhash
    }

    p=subprocess.run(
        [signer_cmd],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        timeout=120
    )

    report["checks"]["signer_return_code"]=p.returncode
    try:
        signer_result=json.loads(p.stdout.strip() or "{}")
    except Exception:
        signer_result={"raw_stdout":p.stdout[-1000:]}

    report["checks"]["signer_result"]=signer_result
    report["checks"]["source_key_match"]=(
        signer_result.get("source")==source and signer_result.get("status")=="signed"
    )
    report["checks"]["signed_transaction_generated"]=bool(
        signer_result.get("signed_transaction_base64")
    )

    # DRY VALIDATION ONLY: no broadcast. We intentionally do not call sendTransaction.
    report["checks"]["broadcast_attempted"]=False

    report["success"]=all([
        report["checks"]["recent_blockhash_available"],
        report["checks"]["source_key_match"],
        report["checks"]["signed_transaction_generated"],
        not report["checks"]["broadcast_attempted"]
    ])
    report["status"]="solana_signer_validation_complete" if report["success"] else "solana_signer_validation_failed"

    OUT.write_text(json.dumps(report,indent=2))
    HEALTH.write_text(json.dumps({"healthy":report["success"],"last_checked_at":now()},indent=2))
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report["success"] else 1)

if __name__=="__main__":
    main()
