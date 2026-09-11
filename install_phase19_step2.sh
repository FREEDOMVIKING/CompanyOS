#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step2_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 2 - External Connector Registry"
echo "============================================================"

for f in "$AGENTS/connector_registry.py" "$CTL/connectorctl" \
 "$MEM/connector_registry_config.json" "$MEM/connector_registry.json" \
 "$MEM/connector_registry_health.json" "$MEM/autonomous_operations_config.json"; do
 [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/connector_registry_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_connector_discovery": true,
  "automatic_health_checks": true,
  "automatic_external_reads": true,
  "automatic_external_writes": false,
  "require_gateway_for_external_actions": true,
  "customer_contact": false,
  "publication": false,
  "spending": false,
  "credential_export": false,
  "private_key_export": false
}
JSON

cat > "$AGENTS/connector_registry.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
CFG=MEM/"connector_registry_config.json"
REG=MEM/"connector_registry.json"
HEALTH=MEM/"connector_registry_health.json"
GATEWAY_CFG=MEM/"execution_gateway_config.json"

DEFAULT_CONNECTORS=[
 {"id":"github","name":"GitHub","type":"code_repository","read":True,"write":True,"enabled":True},
 {"id":"email","name":"Email","type":"communications","read":True,"write":False,"enabled":False},
 {"id":"calendar","name":"Calendar","type":"scheduling","read":True,"write":False,"enabled":False},
 {"id":"crm","name":"CRM","type":"business_data","read":True,"write":False,"enabled":True},
 {"id":"accounting","name":"Accounting","type":"finance_data","read":True,"write":False,"enabled":True},
 {"id":"market-data","name":"Market Data","type":"external_data","read":True,"write":False,"enabled":False}
]

def now(): return datetime.now(timezone.utc).isoformat()
def load(p:Path,d:Any)->Any:
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return d
def save(p:Path,d:Any)->None:
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2),encoding="utf-8")
    t.replace(p)

def discover():
    cfg=load(CFG,{})
    gateway=load(GATEWAY_CFG,{})
    store=load(REG,{"schema_version":1,"connectors":[]})
    existing={x.get("id"):x for x in store.get("connectors",[])}

    for item in DEFAULT_CONNECTORS:
        current=existing.get(item["id"],{})
        merged={**item,**current}
        merged["last_discovered_at"]=now()
        existing[item["id"]]=merged

    connectors=list(existing.values())
    save(REG,{"schema_version":1,"generated_at":now(),"connectors":connectors})

    enabled=sum(1 for x in connectors if x.get("enabled"))
    writable=sum(1 for x in connectors if x.get("enabled") and x.get("write"))

    save(HEALTH,{
      "healthy":True,
      "last_discovered_at":now(),
      "connector_count":len(connectors),
      "enabled_count":enabled,
      "write_capable_count":writable,
      "gateway_present":bool(gateway)
    })

    return {"success":True,"status":"connector_discovery_complete",
            "connectors":connectors}

def status():
    return {"success":True,"status":"connector_registry_status",
            "config":load(CFG,{}),"registry":load(REG,{}),
            "health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=discover() if a=="discover" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["discover","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/connector_registry.py"

cat > "$CTL/connectorctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
 [sys.executable,str(r/"agents"/"connector_registry.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/connectorctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/connector_registry.py" "$CTL/connectorctl"

echo "[2/5] Discovering connectors..."
python "$CTL/connectorctl" discover

echo "[3/5] Adding connector health job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"connector-registry","enabled":True,"interval_seconds":3600,
   "command":["python","companyos/connectorctl","discover"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY

echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/connectorctl" status

echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"connector_registry.py",r/"companyos"/"connectorctl",
r/"ceo_memory"/"connector_registry_config.json",r/"ceo_memory"/"connector_registry.json",
r/"ceo_memory"/"connector_registry_health.json",r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
try:
    c=json.loads(req[2].read_text())
    for k in ["automatic_external_writes","customer_contact","publication","spending",
              "credential_export","private_key_export"]:
        if c.get(k) is not False:errors.append(f"{k} must remain disabled")
    s=json.loads(req[5].read_text())
    j=next((x for x in s.get("jobs",[]) if x.get("id")=="connector-registry"),None)
    if not j or j.get("enabled") is not True:errors.append("Connector registry scheduler job missing/disabled")
except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("Phase 19 Step 2 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 19 STEP 2 INSTALLED"
echo " EXTERNAL CONNECTOR REGISTRY ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/connectorctl discover"
echo "  python companyos/connectorctl status"
