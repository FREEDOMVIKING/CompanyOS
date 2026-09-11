#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step3_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 3 - Connector Capability & Permission Broker"
echo "============================================================"

for f in "$AGENTS/permission_broker.py" "$CTL/permissionctl" \
 "$MEM/permission_broker_config.json" "$MEM/permission_broker_state.json" \
 "$MEM/permission_broker_health.json" "$MEM/autonomous_operations_config.json"; do
 [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/permission_broker_config.json" <<'JSON'
{
  "enabled": true,
  "default_deny": true,
  "allow_automatic_read_only": true,
  "allow_automatic_internal_actions": true,
  "require_owner_approval_for_external_writes": true,
  "require_owner_approval_for_customer_contact": true,
  "require_owner_approval_for_publication": true,
  "require_owner_approval_for_spending": true,
  "require_owner_approval_for_destructive_actions": true,
  "credential_export": false,
  "private_key_export": false
}
JSON

cat > "$AGENTS/permission_broker.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos";M=R/"ceo_memory"
CFG=M/"permission_broker_config.json";REG=M/"connector_registry.json"
STATE=M/"permission_broker_state.json";HEALTH=M/"permission_broker_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def build():
    cfg=load(CFG,{})
    connectors=load(REG,{}).get("connectors",[])
    matrix=[]
    for c in connectors:
        enabled=bool(c.get("enabled"))
        can_read=enabled and bool(c.get("read")) and cfg.get("allow_automatic_read_only",True)
        write_capable=enabled and bool(c.get("write"))
        matrix.append({
          "connector_id":c.get("id"),"enabled":enabled,
          "automatic_read_allowed":can_read,
          "automatic_write_allowed":False,
          "write_capable":write_capable,
          "write_requires_owner_approval":write_capable
        })
    state={"generated_at":now(),"default_deny":True,"permissions":matrix}
    save(STATE,state)
    save(HEALTH,{"healthy":True,"last_built_at":now(),
                 "connector_count":len(matrix),
                 "automatic_read_count":sum(x["automatic_read_allowed"] for x in matrix),
                 "automatic_write_count":0})
    return {"success":True,"status":"permission_matrix_built","state":state}

def status():
    return {"success":True,"status":"permission_broker_status",
            "config":load(CFG,{}),"state":load(STATE,{}),"health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/permission_broker.py"

cat > "$CTL/permissionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
 [sys.executable,str(r/"agents"/"permission_broker.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/permissionctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/permission_broker.py" "$CTL/permissionctl"
echo "[2/5] Building permission matrix..."
python "$CTL/permissionctl" build
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"permission-broker","enabled":True,"interval_seconds":3600,
   "command":["python","companyos/permissionctl","build"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/permissionctl" status
echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"permission_broker.py",r/"companyos"/"permissionctl",
r/"ceo_memory"/"permission_broker_config.json",r/"ceo_memory"/"permission_broker_state.json",
r/"ceo_memory"/"permission_broker_health.json",r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
try:
    c=json.loads(req[2].read_text())
    if c.get("default_deny") is not True:errors.append("default_deny must be enabled")
    for k in ["credential_export","private_key_export"]:
        if c.get(k) is not False:errors.append(f"{k} must remain disabled")
    st=json.loads(req[3].read_text())
    if any(x.get("automatic_write_allowed") for x in st.get("permissions",[])):
        errors.append("Automatic connector writes must remain disabled")
except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("Phase 19 Step 3 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 19 STEP 3 INSTALLED"
echo " CONNECTOR PERMISSION BROKER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/permissionctl build"
echo "  python companyos/permissionctl status"
