#!/usr/bin/env python3
import base64, json, os, shlex, subprocess, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase33a_solana_execution_config.json"
PROPOSALS=MEM/"transaction_proposals.json"
LEDGER=MEM/"crypto_treasury_ledger.json"
OUT=MEM/"solana_execution_report.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def rpc(url,method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json","User-Agent":"CompanyOS/1.0"})
    with urllib.request.urlopen(req,timeout=20) as r:
        j=json.loads(r.read().decode())
    if j.get("error"): raise RuntimeError(f"RPC {method} error: {j['error']}")
    return j.get("result")

def get_proposal(pid):
    for x in load(PROPOSALS,{"proposals":[]}).get("proposals",[]):
        if x.get("proposal_id")==pid:return x
    return None

def update_proposal(pid, **fields):
    q=load(PROPOSALS,{"proposals":[]})
    found=None
    for x in q.get("proposals",[]):
        if x.get("proposal_id")==pid:
            x.update(fields);found=x;break
    save(PROPOSALS,q);return found

def run_signer(cmd_env, payload):
    cmd=os.getenv(cmd_env,"").strip()
    if not cmd:
        raise RuntimeError(f"{cmd_env} is not configured")
    p=subprocess.run(shlex.split(cmd),input=json.dumps(payload),text=True,capture_output=True,timeout=120)
    if p.returncode!=0:
        raise RuntimeError(f"signer_failed rc={p.returncode}: {p.stderr[-1000:]}")
    try:return json.loads(p.stdout)
    except Exception as e:raise RuntimeError(f"signer_invalid_json: {e}")

def execute(pid):
    cfg=load(CFG,{})
    prop=get_proposal(pid)
    if not prop:return {"success":False,"status":"proposal_not_found"}
    if prop.get("chain")!="solana" or prop.get("asset")!="SOL":
        return {"success":False,"status":"unsupported_route","proposal":prop}
    if prop.get("status")!="ready_for_signing" or not prop.get("signing_authorized"):
        return {"success":False,"status":"proposal_not_authorized","proposal":prop}

    rpc_url=os.getenv(cfg.get("rpc_url_env","SOLANA_RPC_URL"),"").strip()
    if not rpc_url:return {"success":False,"status":"rpc_not_configured"}

    # Re-check live balance.
    lamports=int(round(float(prop["amount_native"])*1_000_000_000))
    live=rpc(rpc_url,"getBalance",[prop["source"],{"commitment":"confirmed"}])
    balance=int((live or {}).get("value",0))
    if balance <= lamports:
        return {"success":False,"status":"insufficient_live_balance","balance_lamports":balance,"required_lamports":lamports}

    # Get recent blockhash and delegate exact transaction construction/signing
    # to the isolated local signer process. The private key never enters CompanyOS.
    latest=rpc(rpc_url,"getLatestBlockhash",[{"commitment":"confirmed"}])
    blockhash=(latest or {}).get("value",{}).get("blockhash")
    if not blockhash: return {"success":False,"status":"blockhash_unavailable"}

    signer_payload={
      "action":"build_and_sign_sol_transfer",
      "proposal_id":pid,
      "source":prop["source"],
      "destination":prop["destination"],
      "lamports":lamports,
      "recent_blockhash":blockhash
    }
    signed=run_signer(cfg.get("signer_command_env","SOLANA_SIGNER_COMMAND"),signer_payload)
    signed_tx=signed.get("signed_transaction_base64")
    if not signed_tx:
        return {"success":False,"status":"signer_missing_signed_transaction"}

    # Preflight simulation.
    sim=rpc(rpc_url,"simulateTransaction",[signed_tx,{"encoding":"base64","sigVerify":True,"commitment":"confirmed"}])
    sim_value=(sim or {}).get("value",{})
    if sim_value.get("err") is not None:
        update_proposal(pid,status="preflight_failed",preflight_error=sim_value.get("err"))
        return {"success":False,"status":"preflight_failed","simulation":sim_value}

    # Broadcast.
    sig=rpc(rpc_url,"sendTransaction",[signed_tx,{"encoding":"base64","skipPreflight":False,"preflightCommitment":"confirmed","maxRetries":3}])
    update_proposal(pid,status="broadcast",broadcast_authorized=True,signature=sig,broadcast_at=now())

    # Confirmation tracking.
    deadline=time.time()+int(cfg.get("max_confirmation_wait_seconds",90))
    confirmation=None
    while time.time()<deadline:
        st=rpc(rpc_url,"getSignatureStatuses",[[sig],{"searchTransactionHistory":True}])
        vals=(st or {}).get("value") or []
        x=vals[0] if vals else None
        if x:
            if x.get("err") is not None:
                update_proposal(pid,status="chain_failed",chain_error=x.get("err"))
                return {"success":False,"status":"chain_failed","signature":sig,"chain_status":x}
            cs=x.get("confirmationStatus")
            if cs in ("confirmed","finalized"):
                confirmation=x;break
        time.sleep(2)

    if confirmation is None:
        update_proposal(pid,status="confirmation_pending",signature=sig)
        return {"success":True,"status":"broadcast_confirmation_pending","signature":sig}

    update_proposal(pid,status="confirmed",confirmed_at=now(),signature=sig)
    ledger=load(LEDGER,{"transactions":[]})
    rec=dict(prop)
    rec.update({"direction":"outgoing","status":"confirmed","signature":sig,"confirmed_at":now()})
    ledger["transactions"].append(rec);save(LEDGER,ledger)

    report={"generated_at":now(),"proposal_id":pid,"signature":sig,"status":"confirmed"}
    save(OUT,report)
    return {"success":True,"status":"solana_transaction_confirmed","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="execute":
    r=execute(sys.argv[2])
else:
    cfg=load(CFG,{})
    r={
      "success":True,
      "status":"solana_execution_engine_ready",
      "rpc_configured":bool(os.getenv(cfg.get("rpc_url_env","SOLANA_RPC_URL"),"").strip()),
      "signer_configured":bool(os.getenv(cfg.get("signer_command_env","SOLANA_SIGNER_COMMAND"),"").strip()),
      "automatic_signing":cfg.get("automatic_signing"),
      "automatic_broadcast":cfg.get("automatic_broadcast")
    }
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
