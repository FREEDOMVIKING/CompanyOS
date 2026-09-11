#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
WORKSPACE="$ROOT/workspace"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$WORKSPACE"

echo "============================================================"
echo " Phase 15 Step 6 - Prototype Builder"
echo "============================================================"

cat > "$MEMORY/prototype_builder_config.json" <<'JSON'
{
  "enabled": true,
  "preview_host": "127.0.0.1",
  "preview_port": 8765,
  "automatic_external_deployment": false,
  "automatic_publication": false,
  "automatic_spending": false
}
JSON

cat > "$AGENTS/prototype_builder.py" <<'PY'
#!/usr/bin/env python3
import json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
WORKSPACE = ROOT / "workspace"
PLANS = MEMORY / "product_execution_plans.json"
REGISTRY = MEMORY / "prototype_registry.json"
HEALTH = MEMORY / "prototype_builder_health.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def slug(value):
    text = "".join(c.lower() if c.isalnum() else "_" for c in value)
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or "project"


def latest_plan():
    plans = load(PLANS, {}).get("plans", [])
    if not plans:
        raise RuntimeError("No product execution plan found")
    return plans[-1]


def write_prototype(target):
    frontend = target / "frontend"
    frontend.mkdir(parents=True, exist_ok=True)

    (frontend / "index.html").write_text('''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local Contractor Bid Organizer</title><link rel="stylesheet" href="styles.css"></head>
<body><header><h1>Local Contractor Bid Organizer</h1><p>Track customers, estimates, follow-ups and bid status.</p></header>
<main><form id="bidForm"><input id="customer" placeholder="Customer name" required><input id="project" placeholder="Project name" required><input id="amount" type="number" min="0" step="0.01" placeholder="Estimate amount" required><select id="status"><option value="new">New lead</option><option value="sent">Estimate sent</option><option value="followup">Follow-up due</option><option value="won">Won</option><option value="lost">Lost</option></select><button type="submit">Save Bid</button></form><section><h2>Bid Pipeline</h2><div id="summary"></div><div id="bids"></div></section></main><script src="app.js"></script></body></html>
''', encoding="utf-8")

    (frontend / "styles.css").write_text('''*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:#f3f5f7;color:#17202a}header{padding:24px;background:white;border-bottom:1px solid #d8dee4}header h1{margin:0 0 6px}header p{margin:0}main{width:min(900px,calc(100% - 28px));margin:24px auto}form,section{display:grid;gap:10px;padding:18px;margin-bottom:18px;background:white;border-radius:12px}input,select,button{padding:12px;border:1px solid #c8d0d8;border-radius:8px;font:inherit}button{border:0;background:#1769e0;color:white;font-weight:bold}.bid{padding:12px 0;border-bottom:1px solid #e5e9ed}''', encoding="utf-8")

    (frontend / "app.js").write_text('''const key="companyos_bids";function load(){try{return JSON.parse(localStorage.getItem(key)||"[]")}catch{return[]}}function save(v){localStorage.setItem(key,JSON.stringify(v))}function render(){const bids=load(),list=document.getElementById("bids");const total=bids.reduce((s,b)=>s+Number(b.amount||0),0);document.getElementById("summary").textContent=`${bids.length} bids | Pipeline: $${total.toFixed(2)}`;list.innerHTML="";for(const b of bids){const el=document.createElement("div");el.className="bid";el.textContent=`${b.customer} — ${b.project} — $${Number(b.amount).toFixed(2)} — ${b.status}`;list.appendChild(el)}}document.getElementById("bidForm").addEventListener("submit",e=>{e.preventDefault();const bids=load();bids.push({customer:document.getElementById("customer").value.trim(),project:document.getElementById("project").value.trim(),amount:Number(document.getElementById("amount").value),status:document.getElementById("status").value});save(bids);e.target.reset();render()});render();''', encoding="utf-8")

    (target / "server.py").write_text('''from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
root=Path(__file__).resolve().parent/"frontend"
os.chdir(root)
server=ThreadingHTTPServer(("127.0.0.1",8765),SimpleHTTPRequestHandler)
print("Open http://127.0.0.1:8765")
print("Press Ctrl+C to stop.")
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
''', encoding="utf-8")


def build():
    plan = latest_plan()
    project_name = str(plan.get("project_name") or "project")
    project_id = str(plan.get("project_id") or "unknown")
    root = WORKSPACE / slug(project_name) / "prototype"
    versions = root / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    nums = []
    for item in versions.glob("v*"):
        try: nums.append(int(item.name[1:]))
        except ValueError: pass
    version = max(nums, default=0) + 1
    target = versions / f"v{version}"
    write_prototype(target)
    current = root / "current"
    if current.exists(): shutil.rmtree(current)
    shutil.copytree(target, current)

    registry = load(REGISTRY, {"schema_version":1,"prototypes":[],"statistics":{}})
    records = registry.setdefault("prototypes", [])
    record = {"id":f"prototype-{slug(project_id)}-v{version}","project_id":project_id,"project_name":project_name,"version":version,"status":"ready","directory":str(target),"current_directory":str(current),"preview_url":"http://127.0.0.1:8765","external_deployment_used":False,"external_publication_used":False,"external_spending_used":False,"created_at":now()}
    records.append(record)
    registry["statistics"] = {"total":len(records),"ready":sum(1 for x in records if x.get("status")=="ready"),"failed":sum(1 for x in records if x.get("status")=="failed")}
    registry["last_updated_at"] = now()
    save(REGISTRY, registry)
    save(HEALTH, {"healthy":True,"latest_version":version,"latest_directory":str(current),"last_error":None,"updated_at":now()})
    return {"success":True,"status":"prototype_build_complete","project_name":project_name,"version":version,"current_directory":str(current),"preview_url":"http://127.0.0.1:8765"}


def status():
    return {"success":True,"status":"prototype_builder_status","statistics":load(REGISTRY,{}).get("statistics",{}),"health":load(HEALTH,{}),"automatic_external_deployment":False,"automatic_publication":False,"automatic_spending":False}


def latest():
    records = load(REGISTRY,{}).get("prototypes",[])
    return {"success":bool(records),"status":"latest_prototype","prototype":records[-1] if records else None}


def main():
    action = sys.argv[1] if len(sys.argv)>1 else "status"
    try:
        result = build() if action=="build-latest" else status() if action=="status" else latest() if action=="latest" else {"success":False,"status":"unknown_action","action":action}
    except Exception as exc:
        result = {"success":False,"status":"prototype_builder_error","error":str(exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/prototype_builder.py"

cat > "$CTL/prototypectl" <<'PY'
#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
root=Path.home()/"companyos"
builder=root/"agents"/"prototype_builder.py"
raise SystemExit(subprocess.call([sys.executable,str(builder),*sys.argv[1:]],cwd=root))
PY

chmod +x "$CTL/prototypectl"

python -m py_compile "$AGENTS/prototype_builder.py" "$CTL/prototypectl"
python "$CTL/prototypectl" build-latest
python "$CTL/prototypectl" status
python "$CTL/prototypectl" latest

python - <<'PY'
import json, py_compile
from pathlib import Path
root=Path.home()/"companyos"
errors=[]
builder=root/"agents"/"prototype_builder.py"
control=root/"companyos"/"prototypectl"
registry_path=root/"ceo_memory"/"prototype_registry.json"
for p in [builder,control,registry_path]:
    if not p.exists(): errors.append(f"Missing: {p}")
for p in [builder,control]:
    try: py_compile.compile(str(p),doraise=True)
    except Exception as exc: errors.append(f"Compile error: {exc}")
try:
    records=json.loads(registry_path.read_text(encoding="utf-8")).get("prototypes",[])
    if not records: errors.append("No prototype created")
    else:
        current=Path(records[-1]["current_directory"])
        for p in [current/"frontend"/"index.html",current/"frontend"/"styles.css",current/"frontend"/"app.js",current/"server.py"]:
            if not p.exists(): errors.append(f"Missing prototype file: {p}")
except Exception as exc: errors.append(f"Registry error: {exc}")
print("--------------------------------------------")
print("Phase 15 Step 6 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for error in errors: print(f"ERROR: {error}")
if errors: raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 15 STEP 6 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Start: python workspace/local_contractor_bid_organizer/prototype/current/server.py"
echo "Open: http://127.0.0.1:8765"
