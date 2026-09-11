#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step4_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 4 - Connector Runtime Adapter"
echo "============================================================"

for f in "$AGENTS/connector_runtime.py" "$CTL/runtimectl" \
 "$MEM/connector_runtime_config.json" "$MEM/connector_runtime_state.json" \
 "$MEM/connector_runtime_health.json" "$MEM/connector_runtime_audit.json" \
 "$MEM/autonomous_operations_config.json"; do
 [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/connector_runtime_config.json" <<'JSON'
{
  "enabled": true,
  "require_registered_connector": true,
  "require_permission_broker": true,
  "require_gateway_for_writes": true,
  "automatic_read_only_dispatch": true,
  "automatic_write_dispatch": false,
  "customer_contact": false,
  "publication": false,
  "spending": false,
  "destructive_actions": false,
  "credential_export": false,
  "private_key_export": false
}
JSON

cat > "$AGENTS/connector_runtime.py" <<'PY'
#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"connector_runtime_config.json"; REG=M/"connector_registry.json"
PERM=M/"permission_broker_state.json"; STATE=M/"connector_runtime_state.json"
HEALTH=M/"connector_runtime_health.json"; AUDIT=M/"connector_runtime_audit.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def audit(x):
    a=load(AUDIT,[]); a.append(x); save(AUDIT,a[-2000:])

def resolve(connector_id):
    reg=load(REG,{}).get("connectors",[])
    perm=load(PERM,{}).get("permissions",[])
    c=next((x for x in reg if x.get("id")==connector_id),None)
    p=next((x for x in perm if x.get("connector_id")==connector_id),None)
    if not c:return {"success":False,"status":"connector_not_registered"}
    if not c.get("enabled"):return {"success":False,"status":"connector_disabled"}
    return {"success":True,"connector":c,"permission":p or {}}

def dispatch(connector_id, operation="read"):
    resolved=resolve(connector_id)
    if not resolved.get("success"):
        audit({"timestamp":now(),"connector":connector_id,"operation":operation,"result":resolved})
        return resolved
    p=resolved["permission"]
    if operation=="read":
        allowed=bool(p.get("automatic_read_allowed"))
        result={"success":allowed,
                "status":"read_dispatch_ready" if allowed else "read_not_permitted",
                "connector":connector_id,
                "adapter_status":"interface_ready_no_live_binding"}
    else:
        result={"success":False,"status":"gateway_approval_required",
                "connector":connector_id,"operation":operation}
    audit({"timestamp":now(),"connector":connector_id,"operation":operation,"result":result})
    return result

def build():
    reg=load(REG,{}).get("connectors",[])
    adapters=[]
    for c in reg:
        r=resolve(c.get("id"))
        adapters.append({
          "connector_id":c.get("id"),
          "enabled":bool(c.get("enabled")),
          "runtime_ready":bool(r.get("success")),
          "read_ready":bool(r.get("permission",{}).get("automatic_read_allowed")) if r.get("success") else False,
          "write_route":"execution_gateway"
        })
    state={"generated_at":now(),"adapters":adapters}
    save(STATE,state)
    save(HEALTH,{"healthy":True,"last_built_at":now(),"adapter_count":len(adapters),
                 "runtime_ready_count":sum(x["runtime_ready"] for x in adapters)})
    return {"success":True,"status":"connector_runtime_built","state":state}

def status():
    return {"success":True,"status":"connector_runtime_status",
            "config":load(CFG,{}),"state":load(STATE,{}),"health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="build":r=build()
elif a=="status":r=status()
elif a=="dispatch" and len(sys.argv)>=3:r=dispatch(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else "read")
else:r={"success":False,"status":"unknown_action","allowed":["build","status","dispatch <connector> <read|write>"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/connector_runtime.py"

cat > "$CTL/runtimectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"connector_runtime.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/runtimectl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/connector_runtime.py" "$CTL/runtimectl"
echo "[2/5] Building runtime adapters..."
python "$CTL/runtimectl" build
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text()); jobs=d.setdefault("jobs",[])
j={"id":"connector-runtime","enabled":True,"interval_seconds":3600,
   "command":["python","companyos/runtimectl","build"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/runtimectl" status
echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos"; errors=[]
req=[r/"agents"/"connector_runtime.py",r/"companyos"/"runtimectl",
r/"ceo_memory"/"connector_runtime_config.json",r/"ceo_memory"/"connector_runtime_state.json",
r/"ceo_memory"/"connector_runtime_health.json",r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
try:
 c=json.loads(req[2].read_text())
 for k in ["automatic_write_dispatch","customer_contact","publication","spending",
           "destructive_actions","credential_export","private_key_export"]:
  if c.get(k) is not False:errors.append(f"{k} must remain disabled")
 s=json.loads(req[5].read_text())
 j=next((x for x in s.get("jobs",[]) if x.get("id")=="connector-runtime"),None)
 if not j or j.get("enabled") is not True:errors.append("Connector runtime scheduler job missing/disabled")
except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("Phase 19 Step 4 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 19 STEP 4 INSTALLED"
echo " CONNECTOR RUNTIME ADAPTER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/runtimectl build"
echo "  python companyos/runtimectl status"
echo "  python companyos/runtimectl dispatch github read"
