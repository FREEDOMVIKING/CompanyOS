#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 9 - Learned Opportunity Re-Ranking Engine"
echo "============================================================"

cat > "$MEM/opportunity_rerank_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_reranking": true,
  "alignment_weight": 0.70,
  "learned_outcome_weight": 0.30,
  "minimum_learning_samples": 2,
  "maximum_opportunities": 20,
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/opportunity_learned_reranker.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"opportunity_rerank_config.json"
ALIGN=MEM/"strategic_alignment_report.json"
SCORES=MEM/"opportunity_action_scores.json"
REPORT=MEM/"opportunity_rerank_report.json"
STATE=MEM/"opportunity_rerank_state.json"
HEALTH=MEM/"opportunity_rerank_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)
def clamp(v): return max(0.0,min(100.0,v))

def rerank():
    cfg=load(CFG,{})
    aligned=load(ALIGN,{}).get("aligned_opportunities",[])
    scores=load(SCORES,{}).get("actions",{})
    aw=float(cfg.get("alignment_weight",.70)); lw=float(cfg.get("learned_outcome_weight",.30))
    total=aw+lw or 1.0
    minimum=int(cfg.get("minimum_learning_samples",2))
    maximum=int(cfg.get("maximum_opportunities",20))
    rows=[]

    for opp in aligned[:maximum]:
        oid=str(opp.get("id") or "")
        base=float(opp.get("alignment_score",50))
        related=[v for k,v in scores.items() if oid and k.startswith(oid+"-")]
        learned=50.0; samples=0
        if related:
            samples=sum(int(x.get("samples",0)) for x in related)
            vals=[float(x.get("score",50)) for x in related]
            learned=sum(vals)/len(vals)
        active=samples>=minimum
        final=((base*aw)+(learned*lw))/total if active else base
        rows.append({
          "id":opp.get("id"),"title":opp.get("title"),"category":opp.get("category"),
          "alignment_score":round(base,2),"learned_outcome_score":round(learned,2),
          "learning_samples":samples,"learning_active":active,
          "final_opportunity_score":round(clamp(final),2),
          "source":opp.get("source"),"recommendation":opp.get("recommendation")
        })

    rows.sort(key=lambda x:(x["final_opportunity_score"],x["learning_samples"]),reverse=True)
    for i,x in enumerate(rows,1): x["rank"]=i
    report={"generated_at":now(),"reranked_opportunities":rows,
            "top_opportunity":rows[0]["title"] if rows else None,
            "automatic_external_write":False,"automatic_customer_contact":False,
            "automatic_publication":False,"automatic_spending":False,
            "automatic_code_changes":False,"automatic_merge":False,
            "automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_reranked_at":now(),"opportunity_count":len(rows),
                "top_opportunity":report["top_opportunity"]})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"opportunity_count":len(rows)})
    return {"success":True,"status":"learned_opportunity_reranking_complete","report":report}

def status():
    return {"success":True,"status":"opportunity_rerank_status","state":load(STATE,{}),
            "health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=rerank() if a=="rerank" else status() if a=="status" else {"success":False,"allowed":["rerank","status"]}
print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/opportunity_learned_reranker.py"

cat > "$CTL/opportunityrerankctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"opportunity_learned_reranker.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/opportunityrerankctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/opportunity_learned_reranker.py" "$CTL/opportunityrerankctl"
echo "[2/6] Re-ranking opportunities with learned outcomes..."
python "$CTL/opportunityrerankctl" rerank

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text()); jobs=d.setdefault("jobs",[])
job={"id":"learned-opportunity-reranking","enabled":True,"interval_seconds":21600,
     "command":["python","companyos/opportunityrerankctl","rerank"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/opportunityrerankctl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos"; errors=[]
req=[r/"agents"/"opportunity_learned_reranker.py",r/"companyos"/"opportunityrerankctl",
r/"ceo_memory"/"opportunity_rerank_config.json",r/"ceo_memory"/"opportunity_rerank_state.json",
r/"ceo_memory"/"opportunity_rerank_report.json",r/"ceo_memory"/"opportunity_rerank_health.json",
r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads(req[2].read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads(req[6].read_text())
if not any(x.get("id")=="learned-opportunity-reranking" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------"); print("Phase 21 Step 9 verification")
print(f"Errors: {len(errors)}"); print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 9 INSTALLED"
echo " LEARNED OPPORTUNITY RE-RANKING ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/opportunityrerankctl rerank"
echo "  python companyos/opportunityrerankctl status"
