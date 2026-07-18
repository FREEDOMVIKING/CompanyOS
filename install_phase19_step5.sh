#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step5_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 5 - Live Connector Binding Framework"
echo "============================================================"

for f in "$AGENTS/connector_binding.py" "$CTL/bindingctl" \
 "$MEM/connector_binding_config.json" "$MEM/connector_binding_state.json" \
 "$MEM/connector_binding_health.json" "$MEM/autonomous_operations_config.json"; do
 [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/connector_binding_config.json" <<'JSON'
{
  "enabled": true,
  "environment_only_secrets": true,
  "never_store_secret_values": true,
  "automatic_read_bindings": true,
  "automatic_write_bindings": false,
  "require_gateway_for_writes": true,
  "bindings": {
    "github": {"required_env": ["GITHUB_TOKEN"], "read_only_default": true},
    "email": {"required_env": [], "read_only_default": true},
    "calendar": {"required_env": [], "read_only_default": true},
    "crm": {"required_env": [], "read_only_default": true},
    "accounting": {"required_env": [], "read_only_default": true},
    "market-data": {"required_env": [], "read_only_default": true}
  }
}
JSON

cat > "$AGENTS/connector_binding.py" <<'PY'
#!/usr/bin/env python3
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"connector_binding_config.json"; REG=M/"connector_registry.json"
PERM=M/"permission_broker_state.json"; STATE=M/"connector_binding_state.json"
HEALTH=M/"connector_binding_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def bind():
    cfg=load(CFG,{})
    reg={x.get("id"):x for x in load(REG,{}).get("connectors",[])}
    perms={x.get("connector_id"):x for x in load(PERM,{}).get("permissions",[])}
    rows=[]
    for cid,spec in cfg.get("bindings",{}).items():
        connector=reg.get(cid,{})
        required=spec.get("required_env",[])
        present=[name for name in required if bool(os.getenv(name))]
        missing=[name for name in required if not os.getenv(name)]
        enabled=bool(connector.get("enabled"))
        read_allowed=bool(perms.get(cid,{}).get("automatic_read_allowed"))
        rows.append({
          "connector_id":cid,
          "registered":bool(connector),
          "enabled":enabled,
          "read_allowed":read_allowed,
          "required_environment_variables":required,
          "environment_variables_present":present,
          "environment_variables_missing":missing,
          "secret_values_recorded":False,
          "binding_ready":enabled and read_allowed and not missing,
          "write_route":"execution_gateway"
        })
    state={"generated_at":now(),"bindings":rows}
    save(STATE,state)
    save(HEALTH,{
      "healthy":True,"last_checked_at":now(),"binding_count":len(rows),
      "ready_count":sum(x["binding_ready"] for x in rows),
      "secret_values_recorded":False
    })
    return {"success":True,"status":"connector_binding_check_complete","state":state}

def status():
    return {"success":True,"status":"connector_binding_status",
            "state":load(STATE,{}),"health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=bind() if a=="bind" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["bind","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/connector_binding.py"
cat > "$CTL/bindingctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"connector_binding.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/bindingctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/connector_binding.py" "$CTL/bindingctl"
echo "[2/5] Checking live-binding readiness..."
python "$CTL/bindingctl" bind
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"connector-binding","enabled":True,"interval_seconds":3600,
   "command":["python","companyos/bindingctl","bind"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/bindingctl" status
echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"connector_binding.py",r/"companyos"/"bindingctl",
r/"ceo_memory"/"connector_binding_config.json",r/"ceo_memory"/"connector_binding_state.json",
r/"ceo_memory"/"connector_binding_health.json",r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
try:
 c=json.loads(req[2].read_text())
 if c.get("never_store_secret_values") is not True:errors.append("never_store_secret_values must be true")
 if c.get("automatic_write_bindings") is not False:errors.append("automatic_write_bindings must remain disabled")
 st=json.loads(req[3].read_text())
 if any(x.get("secret_values_recorded") for x in st.get("bindings",[])):
  errors.append("Secret value recording detected")
except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("Phase 19 Step 5 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 19 STEP 5 INSTALLED"
echo " LIVE CONNECTOR BINDING FRAMEWORK ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/bindingctl bind"
echo "  python companyos/bindingctl status"
