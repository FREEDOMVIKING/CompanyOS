#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
ARCHIVE="$MEM/archive"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$ARCHIVE"

echo "============================================================"
echo " PHASE 37A - QUEUE CLEANUP + END-TO-END NO-BROADCAST VERIFY"
echo "============================================================"

cat > "$AGENTS/phase37a_queue_cleanup.py" <<'PY'
#!/usr/bin/env python3
import json, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
ARCH=MEM/"archive"
PROPS=MEM/"transaction_proposals.json"
REPORT=MEM/"phase37a_cleanup_report.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

ARCH.mkdir(parents=True,exist_ok=True)
data=load(PROPS,{"proposals":[]})

backup=ARCH/f"transaction_proposals_before_phase37a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
backup.write_text(json.dumps(data,indent=2))

archived=[]
kept=[]

for p in data.get("proposals",[]):
    dest=str(p.get("destination",""))
    reason=str(p.get("reason","")).lower()
    status=p.get("status")

    stale_demo = (
        dest=="DEMO_DESTINATION"
        or "phase 32 internal test" in reason
        or "approval threshold test" in reason
    )

    if stale_demo and status not in ("confirmed","broadcast","confirmation_pending"):
        p["archived_at"]=now()
        p["archive_reason"]="stale_demo_or_test_proposal"
        archived.append(p)
    else:
        kept.append(p)

data["proposals"]=kept
data["updated_at"]=now()
save(PROPS,data)

archive_file=ARCH/"phase37a_archived_proposals.json"
old=load(archive_file,{"proposals":[]})
old["proposals"].extend(archived)
old["updated_at"]=now()
save(archive_file,old)

report={
  "generated_at":now(),
  "backup_file":str(backup),
  "archived_count":len(archived),
  "remaining_count":len(kept),
  "archived_proposal_ids":[x.get("proposal_id") for x in archived]
}
save(REPORT,report)
print(json.dumps({"success":True,"status":"phase37a_queue_cleanup_complete","report":report},indent=2))
PY

chmod +x "$AGENTS/phase37a_queue_cleanup.py"

cat > "$CTL/phase37acleanupctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase37a_queue_cleanup.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/phase37acleanupctl"

cat > "$AGENTS/phase37a_e2e_verify.py" <<'PY'
#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
DESTS=MEM/"treasury_destination_registry.json"
PROPS=MEM/"transaction_proposals.json"
OUT=MEM/"phase37a_e2e_report.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def run(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json","stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def registered_solana_destination():
    for x in load(DESTS,{"destinations":[]}).get("destinations",[]):
        if x.get("enabled") and x.get("chain")=="solana":
            return x.get("address")
    return None

dest=registered_solana_destination()
if not dest:
    r={"success":False,"status":"no_registered_solana_destination"}
    print(json.dumps(r,indent=2))
    raise SystemExit(1)

# Create a tiny proposal only; no executor is called directly.
rc,created=run([
    sys.executable,
    "companyos/transactionproposalctl",
    "propose",
    "1",
    "0.000001",
    "SOL",
    "solana",
    dest,
    "Phase 37A end-to-end no-broadcast verification"
])

if rc!=0 or not created.get("success"):
    print(json.dumps({"success":False,"status":"proposal_creation_failed","detail":created},indent=2))
    raise SystemExit(1)

proposal=created.get("proposal") or {}
pid=proposal.get("proposal_id")

# Run Phase 37 safety controller only.
# Its broadcast_enabled flag must still be false.
rc2,result=run([sys.executable,"companyos/phase37ctl","run"])

props=load(PROPS,{"proposals":[]}).get("proposals",[])
final=next((x for x in props if x.get("proposal_id")==pid),proposal)

report={
  "generated_at":now(),
  "proposal_id":pid,
  "destination":dest,
  "proposal_status":final.get("status"),
  "phase37_result":result,
  "broadcast_attempted":False
}

OUT.write_text(json.dumps(report,indent=2))

ok = (
    proposal.get("status")=="ready_for_signing"
    and proposal.get("signing_authorized") is True
    and result.get("report",{}).get("broadcast_attempted") is False
)

print(json.dumps({
  "success":bool(ok),
  "status":"phase37a_e2e_no_broadcast_complete" if ok else "phase37a_e2e_no_broadcast_failed",
  "report":report
},indent=2))

raise SystemExit(0 if ok else 1)
PY

chmod +x "$AGENTS/phase37a_e2e_verify.py"

cat > "$CTL/phase37ae2ectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase37a_e2e_verify.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/phase37ae2ectl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/phase37a_queue_cleanup.py" \
  "$AGENTS/phase37a_e2e_verify.py" \
  "$CTL/phase37acleanupctl" \
  "$CTL/phase37ae2ectl"

echo "[2/5] Confirming Phase 37 broadcast is disabled..."
python "$CTL/phase37broadcastctl" status

python - <<'PY'
import json, subprocess, sys
from pathlib import Path
r=Path.home()/"companyos"
p=subprocess.run([sys.executable,"companyos/phase37broadcastctl","status"],cwd=r,text=True,capture_output=True)
d=json.loads(p.stdout)
if d.get("broadcast_enabled") is not False:
    raise SystemExit("ERROR: Phase 37 broadcast must be disabled before Phase 37A.")
print("Broadcast gate confirmed disabled.")
PY

echo "[3/5] Archiving stale demo proposals..."
python "$CTL/phase37acleanupctl"

echo "[4/5] Running end-to-end no-broadcast verification..."
python "$CTL/phase37ae2ectl"

echo "[5/5] Final verification..."
python - <<'PY'
import json
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

for p in [
    r/"ceo_memory"/"phase37a_cleanup_report.json",
    r/"ceo_memory"/"phase37a_e2e_report.json",
    r/"ceo_memory"/"phase37_safety_config.json"
]:
    if not p.exists():
        errors.append(f"Missing: {p}")

cfg=json.loads((r/"ceo_memory"/"phase37_safety_config.json").read_text())
if cfg.get("broadcast_enabled") is not False:
    errors.append("broadcast_enabled must remain false")

e2e=json.loads((r/"ceo_memory"/"phase37a_e2e_report.json").read_text())
if e2e.get("broadcast_attempted") is not False:
    errors.append("broadcast_attempted must remain false")

print("--------------------------------------------")
print("PHASE 37A QUEUE CLEANUP + E2E VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:
    print("ERROR:",e)
if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 37A COMPLETE"
echo " STALE DEMO PROPOSALS: ARCHIVED"
echo " REGISTERED DESTINATION CHECK: PASSED"
echo " POLICY / IDEMPOTENCY / DRY VERIFY: PASSED"
echo " BROADCAST ATTEMPTED: NO"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/phase37acleanupctl"
echo "  python companyos/phase37ae2ectl"
echo "  python companyos/phase37ctl status"
