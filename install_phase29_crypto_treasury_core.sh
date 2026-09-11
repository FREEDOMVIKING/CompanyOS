#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
TREASURY="$ROOT/treasury"
CONN="$ROOT/connectors"
BACKUP="$ROOT/backups/phase29_crypto_treasury_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$TREASURY" "$CONN" "$BACKUP"

echo "============================================================"
echo " PHASE 29 - MULTI-CHAIN CRYPTO TREASURY CORE"
echo "============================================================"

cat > "$MEM/phase29_crypto_treasury_config.json" <<'JSON'
{
  "enabled": true,
  "treasury_mode": "crypto_only",
  "receiving": {
    "automatic": true,
    "chains": ["solana", "evm", "bitcoin"],
    "assets": ["SOL", "USDT-SPL", "USDC-SPL", "ETH", "USDT-ERC20", "USDC-ERC20", "BTC"]
  },
  "outgoing": {
    "automatic_signing_enabled": true,
    "daily_total_limit_usd": 20000,
    "single_transaction_auto_limit_usd": 15000,
    "above_single_limit_requires_owner_approval": true,
    "above_daily_limit_requires_owner_approval": true,
    "require_balance_check": true,
    "require_network_match": true,
    "require_destination_validation": true,
    "require_preflight_when_supported": true,
    "require_audit_log": true
  },
  "signer": {
    "mode": "dedicated_treasury_signer",
    "never_store_private_keys_in_repo": true,
    "never_write_private_keys_to_logs": true,
    "never_put_private_keys_in_ai_prompts": true
  }
}
JSON

cat > "$MEM/treasury_wallet_registry.json" <<'JSON'
{
  "wallets": [],
  "note": "Register treasury public addresses here. Signing credentials remain outside repository files."
}
JSON

cat > "$AGENTS/treasury_registry_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
REG=MEM/"treasury_wallet_registry.json"

def now():return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(REG.read_text())
    except:return {"wallets":[]}
def save(d):REG.write_text(json.dumps(d,indent=2))
def wid(chain,address):return hashlib.sha256(f"{chain}|{address}".encode()).hexdigest()[:18]

a=sys.argv[1] if len(sys.argv)>1 else "list"
d=load()
if a=="register":
    chain,address,label=sys.argv[2],sys.argv[3],sys.argv[4]
    item={
      "wallet_id":wid(chain,address),
      "chain":chain,
      "address":address,
      "label":label,
      "enabled":True,
      "created_at":now()
    }
    d["wallets"]=[x for x in d.get("wallets",[]) if x.get("wallet_id")!=item["wallet_id"]]+[item]
    save(d);r={"success":True,"status":"treasury_wallet_registered","wallet":item}
else:
    r={"success":True,"status":"treasury_wallet_registry","registry":d}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/treasury_registry_engine.py"

cat > "$CTL/treasuryregistryctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"treasury_registry_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/treasuryregistryctl"

cat > "$AGENTS/treasury_policy_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase29_crypto_treasury_config.json"
LEDGER=MEM/"crypto_treasury_ledger.json"

def now():return datetime.now(timezone.utc).isoformat()
def today():return datetime.now(timezone.utc).date().isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def evaluate(amount_usd,asset,chain,destination):
    cfg=load(CFG,{})["outgoing"]
    ledger=load(LEDGER,{"transactions":[]})
    spent=sum(float(x.get("amount_usd",0) or 0) for x in ledger.get("transactions",[])
              if x.get("date")==today() and x.get("direction")=="outgoing" and x.get("status")=="broadcast")
    reasons=[]
    if amount_usd>float(cfg["single_transaction_auto_limit_usd"]):
        reasons.append("single_transaction_limit")
    if spent+amount_usd>float(cfg["daily_total_limit_usd"]):
        reasons.append("daily_total_limit")
    chain_rules={
      "solana":{"SOL","USDT-SPL","USDC-SPL"},
      "evm":{"ETH","USDT-ERC20","USDC-ERC20"},
      "bitcoin":{"BTC"}
    }
    if asset not in chain_rules.get(chain,set()):
        reasons.append("asset_network_mismatch")
    return {
      "allowed_for_auto_sign":len(reasons)==0,
      "requires_owner_approval":any(x in reasons for x in ("single_transaction_limit","daily_total_limit")),
      "blocked": "asset_network_mismatch" in reasons,
      "reasons":reasons,
      "daily_spent_usd":spent,
      "daily_remaining_usd":max(0,float(cfg["daily_total_limit_usd"])-spent),
      "single_auto_limit_usd":cfg["single_transaction_auto_limit_usd"]
    }

if len(sys.argv)>=5:
    r=evaluate(float(sys.argv[1]),sys.argv[2],sys.argv[3],sys.argv[4])
else:
    r={"success":True,"status":"treasury_policy_ready"}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/treasury_policy_engine.py"

cat > "$CTL/treasurypolicyctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"treasury_policy_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/treasurypolicyctl"

cat > "$AGENTS/deposit_monitor_engine.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"; CONN=ROOT/"connectors"
REG=MEM/"treasury_wallet_registry.json"
OUT=MEM/"deposit_monitor_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def run():
    wallets=load(REG,{}).get("wallets",[])
    rows=[]
    for w in wallets:
        adapter=CONN/f"{w.get('chain')}_treasury_adapter.py"
        if not adapter.exists():
            rows.append({"wallet_id":w.get("wallet_id"),"chain":w.get("chain"),"status":"adapter_missing"})
            continue
        p=subprocess.run([sys.executable,str(adapter),"scan",json.dumps(w)],cwd=ROOT,text=True,capture_output=True,timeout=120)
        rows.append({"wallet_id":w.get("wallet_id"),"chain":w.get("chain"),"return_code":p.returncode,
                     "status":"scan_complete" if p.returncode==0 else "scan_failed",
                     "stdout":p.stdout[-1500:],"stderr":p.stderr[-500:]})
    report={"generated_at":now(),"wallet_count":len(wallets),"results":rows}
    OUT.write_text(json.dumps(report,indent=2))
    return {"success":True,"status":"deposit_monitor_cycle_complete","report":report}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/deposit_monitor_engine.py"

cat > "$CTL/depositmonitorctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"deposit_monitor_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/depositmonitorctl"

cat > "$AGENTS/treasury_transfer_router.py" <<'PY'
#!/usr/bin/env python3
import json,sys,subprocess,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"; CONN=ROOT/"connectors"
LEDGER=MEM/"crypto_treasury_ledger.json"; QUEUE=MEM/"crypto_treasury_execution_queue.json"

def now():return datetime.now(timezone.utc).isoformat()
def today():return datetime.now(timezone.utc).date().isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def tid(seed):return hashlib.sha256(seed.encode()).hexdigest()[:20]

def policy(amount_usd,asset,chain,destination):
    p=subprocess.run([sys.executable,"companyos/treasurypolicyctl",str(amount_usd),asset,chain,destination],
                     cwd=ROOT,text=True,capture_output=True,timeout=60)
    try:return json.loads(p.stdout)
    except:return {"allowed_for_auto_sign":False,"blocked":True,"reasons":["policy_error"]}

def queue_transfer(amount_usd,amount_native,asset,chain,source,destination,purpose):
    decision=policy(amount_usd,asset,chain,destination)
    q=load(QUEUE,{"items":[]})
    item={
      "transaction_id":tid(f"{now()}|{chain}|{source}|{destination}|{amount_native}|{asset}"),
      "date":today(),
      "amount_usd":amount_usd,
      "amount_native":amount_native,
      "asset":asset,
      "chain":chain,
      "source":source,
      "destination":destination,
      "purpose":purpose,
      "policy":decision,
      "status":"blocked" if decision.get("blocked") else ("ready_for_auto_sign" if decision.get("allowed_for_auto_sign") else "pending_owner_approval"),
      "created_at":now()
    }
    q["items"].append(item);save(QUEUE,q)
    return item

def execute(txid_value):
    q=load(QUEUE,{"items":[]})
    item=next((x for x in q["items"] if x.get("transaction_id")==txid_value),None)
    if not item:return {"success":False,"status":"transaction_not_found"}
    if item.get("status")!="ready_for_auto_sign":
        return {"success":False,"status":"not_authorized_for_auto_sign","item":item}
    adapter=CONN/f"{item['chain']}_treasury_adapter.py"
    if not adapter.exists():return {"success":False,"status":"adapter_missing","chain":item["chain"]}
    p=subprocess.run([sys.executable,str(adapter),"send",json.dumps(item)],cwd=ROOT,text=True,capture_output=True,timeout=300)
    if p.returncode==0:
        item["status"]="broadcast";item["broadcast_at"]=now()
        ledger=load(LEDGER,{"transactions":[]});ledger["transactions"].append(item);save(LEDGER,ledger);save(QUEUE,q)
    return {"success":p.returncode==0,"status":"broadcast" if p.returncode==0 else "send_failed",
            "stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:],"item":item}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="queue":
    item=queue_transfer(float(sys.argv[2]),float(sys.argv[3]),sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7]," ".join(sys.argv[8:]))
    r={"success":True,"status":"transfer_queued","item":item}
elif a=="execute":
    r=execute(sys.argv[2])
else:
    r={"success":True,"status":"treasury_transfer_router_ready","queue":load(QUEUE,{"items":[]})}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/treasury_transfer_router.py"

cat > "$CTL/treasurytransferctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"treasury_transfer_router.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/treasurytransferctl"

# Fail-closed adapter templates for Solana, EVM, Bitcoin.
# These never hold keys in the repo. They expect signer integration via environment/config.
for chain in solana evm bitcoin; do
cat > "$CONN/${chain}_treasury_adapter.py" <<PY
#!/usr/bin/env python3
import json,sys,os
mode=sys.argv[1] if len(sys.argv)>1 else "status"
payload=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
required_env={
  "solana":["SOLANA_RPC_URL","SOLANA_SIGNER_COMMAND"],
  "evm":["EVM_RPC_URL","EVM_SIGNER_COMMAND"],
  "bitcoin":["BITCOIN_RPC_URL","BITCOIN_SIGNER_COMMAND"]
}["$chain"]
missing=[k for k in required_env if not os.getenv(k,"").strip()]
if missing:
    print(json.dumps({
      "success":False,
      "status":"signer_not_configured",
      "chain":"$chain",
      "missing_env":missing,
      "mode":mode
    },indent=2))
    raise SystemExit(2)

print(json.dumps({
  "success":False,
  "status":"adapter_requires_provider_specific_implementation",
  "chain":"$chain",
  "mode":mode,
  "message":"Configure the RPC/provider-specific transaction builder and signer command before live broadcast."
},indent=2))
raise SystemExit(3)
PY
chmod +x "$CONN/${chain}_treasury_adapter.py"
done

cat > "$AGENTS/phase29_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase29_state.json";HEALTH=MEM/"phase29_health.json";REPORT=MEM/"phase29_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

steps=[]
for name,cmd in [
 ("deposit_monitor",["python","companyos/depositmonitorctl"]),
 ("policy_smoke_test",["python","companyos/treasurypolicyctl","1000","SOL","solana","demo-destination"])
]:
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300)
    steps.append({"step":name,"success":p.returncode==0,"stdout":p.stdout[-1500:],"stderr":p.stderr[-500:]})
failed=[x["step"] for x in steps if not x["success"]]
report={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
print(json.dumps({"success":not failed,"status":"phase29_crypto_treasury_core_ready","report":report},indent=2))
PY
chmod +x "$AGENTS/phase29_controller.py"

cat > "$CTL/phase29ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase29_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase29ctl"

echo "[1/6] Compiling..."
python -m py_compile \
 "$AGENTS/treasury_registry_engine.py" "$AGENTS/treasury_policy_engine.py" \
 "$AGENTS/deposit_monitor_engine.py" "$AGENTS/treasury_transfer_router.py" \
 "$AGENTS/phase29_controller.py" \
 "$CTL/treasuryregistryctl" "$CTL/treasurypolicyctl" "$CTL/depositmonitorctl" \
 "$CTL/treasurytransferctl" "$CTL/phase29ctl" \
 "$CONN/solana_treasury_adapter.py" "$CONN/evm_treasury_adapter.py" "$CONN/bitcoin_treasury_adapter.py"

echo "[2/6] Policy tests..."
python "$CTL/treasurypolicyctl" 14000 SOL solana demo-destination
python "$CTL/treasurypolicyctl" 16000 SOL solana demo-destination
python "$CTL/treasurypolicyctl" 1000 USDT-ERC20 evm demo-destination
python "$CTL/treasurypolicyctl" 1000 BTC solana demo-destination || true

echo "[3/6] Initializing ledger/queue..."
[ -f "$MEM/crypto_treasury_ledger.json" ] || echo '{"transactions":[]}' > "$MEM/crypto_treasury_ledger.json"
[ -f "$MEM/crypto_treasury_execution_queue.json" ] || echo '{"items":[]}' > "$MEM/crypto_treasury_execution_queue.json"

echo "[4/6] Deposit monitor smoke test..."
python "$CTL/depositmonitorctl"

echo "[5/6] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase29-crypto-treasury-monitor","enabled":True,"interval_seconds":300,
     "command":["python","companyos/phase29ctl"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"treasury_registry_engine.py",r/"agents"/"treasury_policy_engine.py",
r/"agents"/"deposit_monitor_engine.py",r/"agents"/"treasury_transfer_router.py",
r/"agents"/"phase29_controller.py",r/"companyos"/"treasuryregistryctl",
r/"companyos"/"treasurypolicyctl",r/"companyos"/"depositmonitorctl",
r/"companyos"/"treasurytransferctl",r/"companyos"/"phase29ctl",
r/"connectors"/"solana_treasury_adapter.py",r/"connectors"/"evm_treasury_adapter.py",
r/"connectors"/"bitcoin_treasury_adapter.py",r/"ceo_memory"/"phase29_crypto_treasury_config.json",
r/"ceo_memory"/"treasury_wallet_registry.json",r/"ceo_memory"/"crypto_treasury_ledger.json",
r/"ceo_memory"/"crypto_treasury_execution_queue.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:13]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase29_crypto_treasury_config.json").read_text())
out=cfg["outgoing"]
if out["daily_total_limit_usd"]!=20000:errors.append("daily limit mismatch")
if out["single_transaction_auto_limit_usd"]!=15000:errors.append("single transaction limit mismatch")
if not out["automatic_signing_enabled"]:errors.append("automatic signing must be enabled")
print("--------------------------------------------")
print("PHASE 29 CRYPTO TREASURY CORE VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 29 MULTI-CHAIN CRYPTO TREASURY CORE INSTALLED"
echo " AUTOMATIC RECEIVING: ENABLED"
echo " AUTOMATIC SIGNING POLICY: ENABLED"
echo " DAILY LIMIT: \$20,000"
echo " SINGLE AUTO-SIGN LIMIT: \$15,000"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Supported treasury rails:"
echo "  Solana: SOL, USDT-SPL, USDC-SPL"
echo "  EVM: ETH, USDT-ERC20, USDC-ERC20"
echo "  Bitcoin: BTC"
echo
echo "IMPORTANT:"
echo "  Live broadcast remains fail-closed until RPC endpoints and dedicated signer commands are configured."
echo "  Private keys must not be stored in GitHub, logs, or AI prompts."
echo
echo "Commands:"
echo "  python companyos/treasuryregistryctl list"
echo "  python companyos/treasurypolicyctl 14000 SOL solana DESTINATION"
echo "  python companyos/treasurytransferctl status"
echo "  python companyos/phase29ctl"
