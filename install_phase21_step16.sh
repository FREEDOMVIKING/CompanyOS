#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 16 - Internal Resource Allocation Planner"
echo "============================================================"

cat > "$MEM/resource_allocation_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_priority_projects": 5,
  "total_attention_units": 100,
  "minimum_units_per_project": 5,
  "automatic_internal_planning": true,
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_fund_transfer": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/internal_resource_allocator.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"resource_allocation_config.json"
PRIORITIES=MEM/"portfolio_resource_priorities.json"
STATE=MEM/"resource_allocation_state.json"
REPORT=MEM/"resource_allocation_report.json"
HEALTH=MEM/"resource_allocation_health.json"
PLAN=MEM/"internal_resource_plan.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def allocate():
    cfg=load(CFG,{})
    rows=load(PRIORITIES,{}).get("candidates",[])
    maximum=int(cfg.get("maximum_priority_projects",5))
    total=max(0,int(cfg.get("total_attention_units",100)))
    minimum=max(0,int(cfg.get("minimum_units_per_project",5)))
    rows=rows[:maximum]
    weights=[max(0.0,num(x.get("resource_readiness_score",0))) for x in rows]
    weight_sum=sum(weights)
    allocations=[]

    if rows:
        base=min(minimum,total//len(rows))
        remaining=max(0,total-(base*len(rows)))
        raw=[(remaining*(w/weight_sum) if weight_sum else remaining/len(rows)) for w in weights]
        extras=[int(x) for x in raw]
        leftover=remaining-sum(extras)
        order=sorted(range(len(raw)),key=lambda i:raw[i]-extras[i],reverse=True)
        for i in order[:leftover]: extras[i]+=1
        for row,extra in zip(rows,extras):
            allocations.append({
              "id":row.get("id"),"title":row.get("title"),"category":row.get("category"),
              "resource_readiness_score":row.get("resource_readiness_score"),
              "attention_units":base+extra,
              "allocation_type":"internal_planning_priority"
            })

    plan={"generated_at":now(),"total_attention_units":total,
          "allocated_units":sum(x["attention_units"] for x in allocations),
          "allocations":allocations,
          "note":"Attention units are internal planning weights only; no money or external resources are moved."}
    save(PLAN,plan)

    report={"generated_at":now(),"candidate_count":len(rows),"allocation_count":len(allocations),
      "allocations":allocations,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,"automatic_fund_transfer":False,
      "automatic_code_changes":False,"automatic_merge":False,"automatic_deploy":False,
      "automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_allocated_at":now(),"allocation_count":len(allocations),
      "allocated_units":plan["allocated_units"]})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"allocation_count":len(allocations)})
    return {"success":True,"status":"internal_resource_allocation_complete","report":report,"plan":plan}

def status():
    return {"success":True,"status":"internal_resource_allocation_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"plan":load(PLAN,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=allocate() if a=="allocate" else status() if a=="status" else {"success":False,"allowed":["allocate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/internal_resource_allocator.py"

cat > "$CTL/resourceallocatectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"internal_resource_allocator.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/resourceallocatectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/internal_resource_allocator.py" "$CTL/resourceallocatectl"
echo "[2/6] Building internal resource plan..."
python "$CTL/resourceallocatectl" allocate
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"internal-resource-allocation","enabled":True,"interval_seconds":21600,
"command":["python","companyos/resourceallocatectl","allocate"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/resourceallocatectl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"internal_resource_allocator.py",r/"companyos"/"resourceallocatectl",
r/"ceo_memory"/"resource_allocation_config.json",r/"ceo_memory"/"resource_allocation_state.json",
r/"ceo_memory"/"resource_allocation_report.json",r/"ceo_memory"/"resource_allocation_health.json",
r/"ceo_memory"/"internal_resource_plan.json",r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads(req[2].read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads(req[7].read_text())
if not any(x.get("id")=="internal-resource-allocation" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 16 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 16 INSTALLED"
echo " INTERNAL RESOURCE ALLOCATION PLANNER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/resourceallocatectl allocate"
echo "  python companyos/resourceallocatectl status"
