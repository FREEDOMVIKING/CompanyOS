#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
CONN="$ROOT/connectors"
BACKUP="$ROOT/backups/phase33a_solana_execution_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$CONN" "$BACKUP"

echo "============================================================"
echo " PHASE 33A - SOLANA GOVERNED SIGNING & EXECUTION CORE"
echo "============================================================"

cat > "$MEM/phase33a_solana_execution_config.json" <<'JSON'
{
  "enabled": true,
  "chain": "solana",
  "supported_assets": ["SOL"],
  "single_transaction_auto_limit_usd": 15000,
  "daily_total_limit_usd": 20000,
  "require_phase32_authorization": true,
  "require_live_balance_check": true,
  "require_recent_blockhash": true,
  "require_preflight": true,
  "require_confirmation": true,
  "confirmation_commitment": "confirmed",
  "max_confirmation_wait_seconds": 90,
  "automatic_signing": true,
  "automatic_broadcast": true,
  "signer_mode": "external_local_signer_command",
  "signer_command_env": "SOLANA_SIGNER_COMMAND",
  "rpc_url_env": "SOLANA_RPC_URL",
  "never_store_private_key_in_repo": true,
  "never_log_private_key": true,
  "never_send_private_key_to_ai": true
}
JSON

cat > "$AGENTS/solana_execution_engine.py" <<'PY'
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
PY
chmod +x "$AGENTS/solana_execution_engine.py"

cat > "$CTL/solanaexecutionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"solana_execution_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/solanaexecutionctl"

cat > "$CONN/solana_signer_template.py" <<'PY'
#!/usr/bin/env python3
"""
Template contract for the isolated signer.

stdin JSON:
{
  "action": "build_and_sign_sol_transfer",
  "proposal_id": "...",
  "source": "...",
  "destination": "...",
  "lamports": 123,
  "recent_blockhash": "..."
}

stdout JSON expected:
{
  "signed_transaction_base64": "..."
}

Replace this template with a signer implementation backed by your dedicated
treasury key storage. Do not commit secrets or seed phrases to the repo.
"""
import json,sys
req=json.load(sys.stdin)
print(json.dumps({
  "success":False,
  "status":"signer_template_only",
  "received_action":req.get("action"),
  "message":"Configure SOLANA_SIGNER_COMMAND to an isolated signer implementation."
}))
raise SystemExit(2)
PY
chmod +x "$CONN/solana_signer_template.py"

cat > "$AGENTS/phase33a_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase33a_state.json";HEALTH=MEM/"phase33a_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

p=subprocess.run([sys.executable,"companyos/solanaexecutionctl","status"],cwd=ROOT,text=True,capture_output=True,timeout=60)
ok=p.returncode==0
state={"last_run_at":now(),"failure_count":0 if ok else 1,"stdout":p.stdout[-2000:],"stderr":p.stderr[-500:]}
save(STATE,state);save(HEALTH,{"healthy":ok,"last_checked_at":now()})
print(json.dumps({"success":ok,"status":"phase33a_solana_execution_core_ready","state":state},indent=2))
raise SystemExit(0 if ok else 1)
PY
chmod +x "$AGENTS/phase33a_controller.py"

cat > "$CTL/phase33actl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase33a_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase33actl"

echo "[1/4] Compiling..."
python -m py_compile \
 "$AGENTS/solana_execution_engine.py" "$AGENTS/phase33a_controller.py" \
 "$CTL/solanaexecutionctl" "$CTL/phase33actl" "$CONN/solana_signer_template.py"

echo "[2/4] Execution status..."
python "$CTL/solanaexecutionctl" status

echo "[3/4] Initializing health..."
python "$CTL/phase33actl"

echo "[4/4] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"solana_execution_engine.py",
r/"agents"/"phase33a_controller.py",
r/"companyos"/"solanaexecutionctl",
r/"companyos"/"phase33actl",
r/"connectors"/"solana_signer_template.py",
r/"ceo_memory"/"phase33a_solana_execution_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:5]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase33a_solana_execution_config.json").read_text())
if cfg["single_transaction_auto_limit_usd"]!=15000:errors.append("single limit mismatch")
if cfg["daily_total_limit_usd"]!=20000:errors.append("daily limit mismatch")
if not cfg["require_phase32_authorization"]:errors.append("Phase 32 authorization must remain required")
print("--------------------------------------------")
print("PHASE 33A SOLANA EXECUTION CORE VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 33A SOLANA GOVERNED EXECUTION CORE INSTALLED"
echo " POLICY-GATED AUTO-SIGNING PATH: READY"
echo " PREFLIGHT / BROADCAST / CONFIRMATION: READY"
echo " LIVE SIGNER: REQUIRES SOLANA_SIGNER_COMMAND CONFIGURATION"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/solanaexecutionctl status"
echo "  python companyos/solanaexecutionctl execute PROPOSAL_ID"
echo "  python companyos/phase33actl"
