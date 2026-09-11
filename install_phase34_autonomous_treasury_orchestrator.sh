#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase34_autonomous_treasury_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 34 - AUTONOMOUS TREASURY EXECUTION ORCHESTRATOR"
echo "============================================================"

cat > "$MEM/phase34_autonomous_treasury_config.json" <<'JSON'
{
  "enabled": true,
  "execution_mode": "policy_gated_autonomous",
  "single_transaction_auto_limit_usd": 15000,
  "daily_total_limit_usd": 20000,
  "max_transactions_per_cycle": 5,
  "minimum_seconds_between_broadcasts": 10,
  "require_phase32_authorization": true,
  "require_registered_destination": true,
  "require_live_balance_check": true,
  "require_preflight": true,
  "require_confirmation": true,
  "stop_on_first_execution_failure": true,
  "automatic_receiving": true,
  "automatic_execution": true,
  "automatic_signing": true,
  "automatic_broadcast": true,
  "kill_switch": false,
  "supported_live_routes": {
    "solana": ["SOL"]
  },
  "future_routes": {
    "solana": ["USDT-SPL", "USDC-SPL"],
    "evm": ["ETH", "USDT-ERC20", "USDC-ERC20"],
    "bitcoin": ["BTC"]
  }
}
JSON

cat > "$MEM/treasury_destination_registry.json" <<'JSON'
{
  "destinations": [],
  "note": "Only registered destinations are eligible for autonomous outgoing execution."
}
JSON

cat > "$AGENTS/treasury_destination_registry.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
REG=MEM/"treasury_destination_registry.json"

def now():return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(REG.read_text())
    except:return {"destinations":[]}
def save(d):REG.write_text(json.dumps(d,indent=2))
def did(chain,address):return hashlib.sha256(f"{chain}|{address}".encode()).hexdigest()[:18]

a=sys.argv[1] if len(sys.argv)>1 else "list"
d=load()

if a=="register":
    chain,address,label=sys.argv[2],sys.argv[3],sys.argv[4]
    row={
      "destination_id":did(chain,address),
      "chain":chain,
      "address":address,
      "label":label,
      "enabled":True,
      "created_at":now()
    }
    d["destinations"]=[x for x in d.get("destinations",[]) if x.get("destination_id")!=row["destination_id"]]+[row]
    save(d);r={"success":True,"status":"destination_registered","destination":row}

elif a=="disable":
    ident=sys.argv[2];found=None
    for x in d.get("destinations",[]):
        if x.get("destination_id")==ident or x.get("address")==ident:
            x["enabled"]=False;x["updated_at"]=now();found=x
    save(d);r={"success":bool(found),"status":"destination_disabled","destination":found}

elif a=="enable":
    ident=sys.argv[2];found=None
    for x in d.get("destinations",[]):
        if x.get("destination_id")==ident or x.get("address")==ident:
            x["enabled"]=True;x["updated_at"]=now();found=x
    save(d);r={"success":bool(found),"status":"destination_enabled","destination":found}

else:
    r={"success":True,"status":"destination_registry","registry":d}

print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/treasury_destination_registry.py"

cat > "$CTL/treasurydestinationctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"treasury_destination_registry.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/treasurydestinationctl"

cat > "$AGENTS/autonomous_treasury_orchestrator.py" <<'PY'
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
PY
chmod +x "$AGENTS/autonomous_treasury_orchestrator.py"

cat > "$CTL/autonomoustreasuryctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"autonomous_treasury_orchestrator.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/autonomoustreasuryctl"

cat > "$AGENTS/treasury_kill_switch.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path.home()/"companyos";P=ROOT/"ceo_memory"/"phase34_autonomous_treasury_config.json"
d=json.loads(P.read_text())
a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="on":d["kill_switch"]=True;P.write_text(json.dumps(d,indent=2))
elif a=="off":d["kill_switch"]=False;P.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"status":"treasury_kill_switch","kill_switch":d.get("kill_switch",False)},indent=2))
PY
chmod +x "$AGENTS/treasury_kill_switch.py"

cat > "$CTL/treasurykillswitchctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"treasury_kill_switch.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/treasurykillswitchctl"

cat > "$AGENTS/phase34_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase34_health.json"

def now():return datetime.now(timezone.utc).isoformat()

checks=[]
for name,cmd in [
  ("treasury_monitor",[sys.executable,"companyos/phase31ctl"]),
  ("autonomous_treasury_status",[sys.executable,"companyos/autonomoustreasuryctl","status"])
]:
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300)
    checks.append({"name":name,"success":p.returncode==0,"stdout":p.stdout[-2000:],"stderr":p.stderr[-500:]})

ok=all(x["success"] for x in checks)
STATE.write_text(json.dumps({"healthy":ok,"last_checked_at":now(),"checks":checks},indent=2))
print(json.dumps({"success":ok,"status":"phase34_autonomous_treasury_ready","checks":checks},indent=2))
raise SystemExit(0 if ok else 1)
PY
chmod +x "$AGENTS/phase34_controller.py"

cat > "$CTL/phase34ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase34_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase34ctl"

echo "[1/5] Compiling..."
python -m py_compile \
 "$AGENTS/treasury_destination_registry.py" \
 "$AGENTS/autonomous_treasury_orchestrator.py" \
 "$AGENTS/treasury_kill_switch.py" \
 "$AGENTS/phase34_controller.py" \
 "$CTL/treasurydestinationctl" \
 "$CTL/autonomoustreasuryctl" \
 "$CTL/treasurykillswitchctl" \
 "$CTL/phase34ctl"

echo "[2/5] Initializing state..."
[ -f "$MEM/phase34_autonomous_treasury_audit.jsonl" ] || touch "$MEM/phase34_autonomous_treasury_audit.jsonl"

echo "[3/5] Status check..."
python "$CTL/autonomoustreasuryctl" status
python "$CTL/treasurykillswitchctl" status

echo "[4/5] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase34-autonomous-treasury","enabled":True,"interval_seconds":60,
     "command":["python","companyos/autonomoustreasuryctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[5/5] Verifying..."
python "$CTL/phase34ctl"

python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
 r/"agents"/"treasury_destination_registry.py",
 r/"agents"/"autonomous_treasury_orchestrator.py",
 r/"agents"/"treasury_kill_switch.py",
 r/"agents"/"phase34_controller.py",
 r/"companyos"/"treasurydestinationctl",
 r/"companyos"/"autonomoustreasuryctl",
 r/"companyos"/"treasurykillswitchctl",
 r/"companyos"/"phase34ctl",
 r/"ceo_memory"/"phase34_autonomous_treasury_config.json",
 r/"ceo_memory"/"treasury_destination_registry.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:8]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase34_autonomous_treasury_config.json").read_text())
if cfg["single_transaction_auto_limit_usd"]!=15000:errors.append("single limit mismatch")
if cfg["daily_total_limit_usd"]!=20000:errors.append("daily limit mismatch")
if not cfg["automatic_execution"]:errors.append("automatic execution not enabled")
if not cfg["automatic_signing"]:errors.append("automatic signing not enabled")
if not cfg["automatic_broadcast"]:errors.append("automatic broadcast not enabled")
print("--------------------------------------------")
print("PHASE 34 AUTONOMOUS TREASURY VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 34 AUTONOMOUS TREASURY ORCHESTRATOR INSTALLED"
echo " POLICY-GATED AUTOMATIC EXECUTION: ENABLED"
echo " SOLANA SOL LIVE ROUTE: ENABLED"
echo " SINGLE AUTO LIMIT: \$15,000"
echo " DAILY AUTO LIMIT: \$20,000"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "IMPORTANT:"
echo "  Autonomous outgoing transfers only execute to registered destinations."
echo "  Use the kill switch at any time:"
echo "    python companyos/treasurykillswitchctl on"
echo "    python companyos/treasurykillswitchctl off"
echo
echo "Commands:"
echo "  python companyos/treasurydestinationctl list"
echo "  python companyos/autonomoustreasuryctl status"
echo "  python companyos/autonomoustreasuryctl run"
echo "  python companyos/phase34ctl"
