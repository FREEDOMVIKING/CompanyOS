#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase35_ceo_treasury_bridge_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 35 - CEO TO TREASURY EXECUTION BRIDGE"
echo "============================================================"

cat > "$MEM/phase35_ceo_treasury_bridge_config.json" <<'JSON'
{
  "enabled": true,
  "mode": "governed_autonomous_execution",
  "require_structured_ceo_request": true,
  "require_phase32_policy": true,
  "require_registered_destination": true,
  "require_supported_live_route": true,
  "require_live_balance_check": true,
  "require_preflight": true,
  "require_confirmation": true,
  "single_transaction_auto_limit_usd": 15000,
  "daily_total_limit_usd": 20000,
  "max_ceo_requests_per_cycle": 10,
  "supported_live_routes": {
    "solana": ["SOL"]
  },
  "unsupported_routes_fail_closed": true,
  "automatic_execution": true,
  "automatic_signing": true,
  "automatic_broadcast": true
}
JSON

cat > "$MEM/ceo_treasury_requests.json" <<'JSON'
{
  "requests": []
}
JSON

cat > "$AGENTS/ceo_treasury_request_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase35_ceo_treasury_bridge_config.json"
REQ=MEM/"ceo_treasury_requests.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2)); t.replace(p)
def rid(seed): return hashlib.sha256(seed.encode()).hexdigest()[:22]

def create(amount_usd, amount_native, asset, chain, destination, reason, source_decision_id):
    cfg=load(CFG,{})
    routes=cfg.get("supported_live_routes",{})
    route_supported=asset in routes.get(chain,[])
    row={
      "request_id":rid(f"{now()}|{chain}|{asset}|{destination}|{amount_native}|{source_decision_id}"),
      "created_at":now(),
      "source":"ceo",
      "source_decision_id":source_decision_id,
      "chain":chain,
      "asset":asset,
      "destination":destination,
      "amount_native":amount_native,
      "amount_usd":amount_usd,
      "reason":reason,
      "route_supported":route_supported,
      "status":"pending_bridge" if route_supported else "blocked_unsupported_route"
    }
    d=load(REQ,{"requests":[]}); d["requests"].append(row); d["updated_at"]=now(); save(REQ,d)
    return row

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="create":
    if len(sys.argv)<9:
        r={"success":False,"status":"missing_arguments"}
    else:
        row=create(float(sys.argv[2]),float(sys.argv[3]),sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7],sys.argv[8])
        r={"success":True,"status":"ceo_treasury_request_created","request":row}
else:
    r={"success":True,"status":"ceo_treasury_request_status","queue":load(REQ,{"requests":[]})}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/ceo_treasury_request_engine.py"

cat > "$CTL/ceotreasuryrequestctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ceo_treasury_request_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/ceotreasuryrequestctl"

cat > "$AGENTS/ceo_treasury_bridge_engine.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase35_ceo_treasury_bridge_config.json"
REQ=MEM/"ceo_treasury_requests.json"
AUDIT=MEM/"phase35_ceo_treasury_audit.jsonl"
REPORT=MEM/"phase35_ceo_treasury_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def audit(x):
    with AUDIT.open("a") as f:f.write(json.dumps({"at":now(),**x})+"\n")
def run_cmd(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def cycle():
    cfg=load(CFG,{})
    q=load(REQ,{"requests":[]})
    pending=[x for x in q.get("requests",[]) if x.get("status")=="pending_bridge"]
    results=[]

    for x in pending[:int(cfg.get("max_ceo_requests_per_cycle",10))]:
        rid=x["request_id"]

        # Create governed Phase 32 proposal.
        rc,propres=run_cmd([
          sys.executable,"companyos/transactionproposalctl","propose",
          str(x["amount_usd"]),str(x["amount_native"]),x["asset"],x["chain"],x["destination"],x["reason"]
        ])

        if rc!=0 or not propres.get("success"):
            x["status"]="bridge_failed"
            x["bridge_error"]="proposal_creation_failed"
            row={"request_id":rid,"success":False,"status":"proposal_creation_failed","detail":propres}
            results.append(row);audit(row);continue

        proposal=propres.get("proposal") or {}
        x["proposal_id"]=proposal.get("proposal_id")
        x["proposal_status"]=proposal.get("status")

        if proposal.get("status")=="blocked":
            x["status"]="blocked_by_policy"
            row={"request_id":rid,"success":False,"status":"blocked_by_policy","proposal":proposal}
            results.append(row);audit(row);continue

        if proposal.get("status")=="pending_owner_approval":
            x["status"]="pending_owner_approval"
            row={"request_id":rid,"success":True,"status":"pending_owner_approval","proposal":proposal}
            results.append(row);audit(row);continue

        # Let Phase 34 enforce registered destination + supported live route + executor.
        rc2,execres=run_cmd([sys.executable,"companyos/autonomoustreasuryctl","run"])

        # Refresh proposal state after autonomous cycle.
        props=load(MEM/"transaction_proposals.json",{"proposals":[]}).get("proposals",[])
        updated=next((p for p in props if p.get("proposal_id")==proposal.get("proposal_id")),proposal)
        x["proposal_status"]=updated.get("status")

        if updated.get("status") in ("confirmed","broadcast","confirmation_pending"):
            x["status"]="executed"
            x["completed_at"]=now()
            row={"request_id":rid,"success":True,"status":"executed","proposal":updated,"autonomous_cycle":execres}
        else:
            x["status"]="bridge_submitted"
            row={"request_id":rid,"success":True,"status":"bridge_submitted","proposal":updated,"autonomous_cycle":execres}

        results.append(row);audit(row)

    q["updated_at"]=now();save(REQ,q)
    report={"generated_at":now(),"pending_count":len(pending),"result_count":len(results),"results":results}
    save(REPORT,report)
    return {"success":True,"status":"ceo_treasury_bridge_cycle_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "run"
if a=="status":
    r={"success":True,"status":"ceo_treasury_bridge_status","config":load(CFG,{}),"requests":load(REQ,{"requests":[]})}
else:
    r=cycle()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/ceo_treasury_bridge_engine.py"

cat > "$CTL/ceotreasurybridgectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ceo_treasury_bridge_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/ceotreasurybridgectl"

cat > "$AGENTS/phase35_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
HEALTH=MEM/"phase35_health.json"

def now():return datetime.now(timezone.utc).isoformat()

checks=[]
for name,cmd in [
  ("phase34",[sys.executable,"companyos/phase34ctl"]),
  ("bridge_status",[sys.executable,"companyos/ceotreasurybridgectl","status"])
]:
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300)
    checks.append({"name":name,"success":p.returncode==0,"stdout":p.stdout[-2000:],"stderr":p.stderr[-500:]})
ok=all(x["success"] for x in checks)
HEALTH.write_text(json.dumps({"healthy":ok,"last_checked_at":now(),"checks":checks},indent=2))
print(json.dumps({"success":ok,"status":"phase35_ceo_treasury_bridge_ready","checks":checks},indent=2))
raise SystemExit(0 if ok else 1)
PY
chmod +x "$AGENTS/phase35_controller.py"

cat > "$CTL/phase35ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase35_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase35ctl"

echo "[1/5] Compiling..."
python -m py_compile \
 "$AGENTS/ceo_treasury_request_engine.py" \
 "$AGENTS/ceo_treasury_bridge_engine.py" \
 "$AGENTS/phase35_controller.py" \
 "$CTL/ceotreasuryrequestctl" \
 "$CTL/ceotreasurybridgectl" \
 "$CTL/phase35ctl"

echo "[2/5] Initializing audit..."
[ -f "$MEM/phase35_ceo_treasury_audit.jsonl" ] || touch "$MEM/phase35_ceo_treasury_audit.jsonl"

echo "[3/5] Bridge status..."
python "$CTL/ceotreasurybridgectl" status

echo "[4/5] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase35-ceo-treasury-bridge","enabled":True,"interval_seconds":60,
     "command":["python","companyos/ceotreasurybridgectl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[5/5] Verifying..."
python "$CTL/phase35ctl"

python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
 r/"agents"/"ceo_treasury_request_engine.py",
 r/"agents"/"ceo_treasury_bridge_engine.py",
 r/"agents"/"phase35_controller.py",
 r/"companyos"/"ceotreasuryrequestctl",
 r/"companyos"/"ceotreasurybridgectl",
 r/"companyos"/"phase35ctl",
 r/"ceo_memory"/"phase35_ceo_treasury_bridge_config.json",
 r/"ceo_memory"/"ceo_treasury_requests.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:6]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase35_ceo_treasury_bridge_config.json").read_text())
if cfg["single_transaction_auto_limit_usd"]!=15000:errors.append("single limit mismatch")
if cfg["daily_total_limit_usd"]!=20000:errors.append("daily limit mismatch")
if cfg["supported_live_routes"]!={"solana":["SOL"]}:errors.append("live route map must remain SOL-only")
if not cfg["unsupported_routes_fail_closed"]:errors.append("unsupported routes must fail closed")
print("--------------------------------------------")
print("PHASE 35 CEO TREASURY BRIDGE VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 35 CEO TO TREASURY EXECUTION BRIDGE INSTALLED"
echo " CEO REQUEST -> POLICY -> ALLOWLIST -> EXECUTION PATH: ACTIVE"
echo " SOLANA SOL LIVE ROUTE: ACTIVE"
echo " UNSUPPORTED ROUTES: FAIL-CLOSED"
echo " SINGLE AUTO LIMIT: \$15,000"
echo " DAILY AUTO LIMIT: \$20,000"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/ceotreasuryrequestctl status"
echo "  python companyos/ceotreasurybridgectl status"
echo "  python companyos/ceotreasurybridgectl run"
echo "  python companyos/phase35ctl"
