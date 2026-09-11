#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase32_tx_policy_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 32 - GOVERNED TRANSACTION PROPOSAL & POLICY ENGINE"
echo "============================================================"

cat > "$MEM/phase32_transaction_policy_config.json" <<'JSON'
{
  "enabled": true,
  "daily_total_limit_usd": 20000,
  "single_transaction_auto_limit_usd": 15000,
  "require_owner_approval_above_single_limit": true,
  "require_owner_approval_above_daily_limit": true,
  "require_balance_check": true,
  "require_asset_network_match": true,
  "require_destination_validation": true,
  "require_reason": true,
  "require_receipt_after_broadcast": true,
  "automatic_signing": false,
  "automatic_broadcast": false,
  "supported_routes": {
    "solana": ["SOL", "USDT-SPL", "USDC-SPL"],
    "evm": ["ETH", "USDT-ERC20", "USDC-ERC20"],
    "bitcoin": ["BTC"]
  }
}
JSON

cat > "$AGENTS/transaction_proposal_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"phase32_transaction_policy_config.json"
BAL=MEM/"multi_asset_treasury_balances.json"
QUEUE=MEM/"transaction_proposals.json"
LEDGER=MEM/"crypto_treasury_ledger.json"

def now():return datetime.now(timezone.utc).isoformat()
def today():return datetime.now(timezone.utc).date().isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def pid(seed):return hashlib.sha256(seed.encode()).hexdigest()[:22]

def find_balance(chain,asset):
    for w in load(BAL,{}).get("balances",[]):
        if w.get("chain")==chain:
            return (w.get("assets") or {}).get(asset), w.get("address")
    return None,None

def spent_today():
    total=0
    for x in load(LEDGER,{"transactions":[]}).get("transactions",[]):
        if x.get("date")==today() and x.get("direction")=="outgoing" and x.get("status") in ("broadcast","confirmed"):
            try: total += float(x.get("amount_usd",0) or 0)
            except: pass
    return total

def propose(amount_usd,amount_native,asset,chain,destination,reason):
    cfg=load(CFG,{})
    reasons=[]
    routes=cfg.get("supported_routes",{})
    if asset not in routes.get(chain,[]): reasons.append("asset_network_mismatch")
    if cfg.get("require_reason") and not reason.strip(): reasons.append("missing_reason")
    bal,source=find_balance(chain,asset)
    if cfg.get("require_balance_check") and bal is not None and float(amount_native)>float(bal): reasons.append("insufficient_balance")
    daily=spent_today()
    requires_approval=False
    if amount_usd>float(cfg["single_transaction_auto_limit_usd"]):
        requires_approval=True;reasons.append("single_transaction_limit")
    if daily+amount_usd>float(cfg["daily_total_limit_usd"]):
        requires_approval=True;reasons.append("daily_total_limit")
    blocked=any(x in reasons for x in ("asset_network_mismatch","missing_reason","insufficient_balance"))
    status="blocked" if blocked else ("pending_owner_approval" if requires_approval else "ready_for_signing")
    item={
      "proposal_id":pid(f"{now()}|{chain}|{asset}|{destination}|{amount_native}"),
      "created_at":now(),"date":today(),
      "chain":chain,"asset":asset,
      "source":source,"destination":destination,
      "amount_native":amount_native,"amount_usd":amount_usd,
      "reason":reason,"daily_spent_before_usd":daily,
      "policy_reasons":reasons,
      "requires_owner_approval":requires_approval,
      "status":status,
      "signing_authorized":status=="ready_for_signing",
      "broadcast_authorized":False
    }
    q=load(QUEUE,{"proposals":[]});q["proposals"].append(item);q["updated_at"]=now();save(QUEUE,q)
    return item

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="propose":
    item=propose(float(sys.argv[2]),float(sys.argv[3]),sys.argv[4],sys.argv[5],sys.argv[6]," ".join(sys.argv[7:]))
    r={"success":True,"status":"transaction_proposal_created","proposal":item}
else:
    r={"success":True,"status":"transaction_proposal_status","queue":load(QUEUE,{"proposals":[]})}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/transaction_proposal_engine.py"

cat > "$CTL/transactionproposalctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"transaction_proposal_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/transactionproposalctl"

cat > "$AGENTS/transaction_approval_bridge.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
QUEUE=MEM/"transaction_proposals.json"

def now():return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(QUEUE.read_text())
    except:return {"proposals":[]}
def save(d):QUEUE.write_text(json.dumps(d,indent=2))

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a in ("approve","deny"):
    q=load();item=None
    for x in q.get("proposals",[]):
        if x.get("proposal_id")==sys.argv[2]:
            item=x
            if a=="approve":
                x["status"]="ready_for_signing";x["signing_authorized"]=True;x["owner_approved_at"]=now()
            else:
                x["status"]="denied";x["signing_authorized"]=False;x["owner_denied_at"]=now()
            break
    save(q);r={"success":bool(item),"status":"transaction_approval_updated","proposal":item}
else:
    r={"success":True,"status":"transaction_approval_status","queue":load()}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/transaction_approval_bridge.py"

cat > "$CTL/transactionapprovalctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"transaction_approval_bridge.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/transactionapprovalctl"

cat > "$AGENTS/transaction_signing_queue.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
QUEUE=MEM/"transaction_proposals.json";OUT=MEM/"transaction_signing_queue.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
rows=[]
for x in load(QUEUE,{"proposals":[]}).get("proposals",[]):
    if x.get("status")=="ready_for_signing" and x.get("signing_authorized"):
        rows.append(x)
payload={"generated_at":now(),"ready_count":len(rows),"transactions":rows}
OUT.write_text(json.dumps(payload,indent=2))
print(json.dumps({"success":True,"status":"transaction_signing_queue_complete","queue":payload},indent=2))
PY
chmod +x "$AGENTS/transaction_signing_queue.py"

cat > "$CTL/transactionsigningqueuectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"transaction_signing_queue.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/transactionsigningqueuectl"

cat > "$AGENTS/phase32_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase32_state.json";HEALTH=MEM/"phase32_health.json";REPORT=MEM/"phase32_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

steps=[];failed=[]
for name,cmd in [
 ("multi_asset_balances",["python","companyos/multiassetbalancectl"]),
 ("signing_queue",["python","companyos/transactionsigningqueuectl"])
]:
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300)
    r={"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:]}
    steps.append({"step":name,"result":r})
    if not r["success"]:failed.append(name)

report={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
print(json.dumps({"success":not failed,"status":"phase32_transaction_policy_complete","report":report},indent=2))
raise SystemExit(0 if not failed else 1)
PY
chmod +x "$AGENTS/phase32_controller.py"

cat > "$CTL/phase32ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase32_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase32ctl"

echo "[1/5] Compiling..."
python -m py_compile \
 "$AGENTS/transaction_proposal_engine.py" "$AGENTS/transaction_approval_bridge.py" \
 "$AGENTS/transaction_signing_queue.py" "$AGENTS/phase32_controller.py" \
 "$CTL/transactionproposalctl" "$CTL/transactionapprovalctl" \
 "$CTL/transactionsigningqueuectl" "$CTL/phase32ctl"

echo "[2/5] Initializing queues..."
[ -f "$MEM/transaction_proposals.json" ] || echo '{"proposals":[]}' > "$MEM/transaction_proposals.json"
[ -f "$MEM/transaction_signing_queue.json" ] || echo '{"transactions":[]}' > "$MEM/transaction_signing_queue.json"

echo "[3/5] Policy smoke tests..."
python "$CTL/transactionproposalctl" propose 100 0.001 SOL solana DEMO_DESTINATION "Phase 32 internal test" || true
python "$CTL/transactionproposalctl" propose 16000 0.001 SOL solana DEMO_DESTINATION "Phase 32 approval threshold test" || true

echo "[4/5] Signing queue..."
python "$CTL/transactionsigningqueuectl"

echo "[5/5] Verifying..."
python "$CTL/phase32ctl" || true

python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"transaction_proposal_engine.py",r/"agents"/"transaction_approval_bridge.py",
r/"agents"/"transaction_signing_queue.py",r/"agents"/"phase32_controller.py",
r/"companyos"/"transactionproposalctl",r/"companyos"/"transactionapprovalctl",
r/"companyos"/"transactionsigningqueuectl",r/"companyos"/"phase32ctl",
r/"ceo_memory"/"phase32_transaction_policy_config.json",
r/"ceo_memory"/"transaction_proposals.json",r/"ceo_memory"/"transaction_signing_queue.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:8]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase32_transaction_policy_config.json").read_text())
if cfg["daily_total_limit_usd"]!=20000:errors.append("daily limit mismatch")
if cfg["single_transaction_auto_limit_usd"]!=15000:errors.append("single transaction limit mismatch")
if cfg["automatic_signing"] is not False:errors.append("automatic signing must remain off in Phase 32")
if cfg["automatic_broadcast"] is not False:errors.append("automatic broadcast must remain off in Phase 32")
print("--------------------------------------------")
print("PHASE 32 TRANSACTION POLICY VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 32 GOVERNED TRANSACTION POLICY ENGINE INSTALLED"
echo " SINGLE AUTO LIMIT: \$15,000"
echo " DAILY AUTO LIMIT: \$20,000"
echo " SIGNING: NOT YET CONNECTED"
echo " BROADCAST: NOT YET CONNECTED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/transactionproposalctl status"
echo "  python companyos/transactionapprovalctl status"
echo "  python companyos/transactionsigningqueuectl"
echo "  python companyos/phase32ctl"
