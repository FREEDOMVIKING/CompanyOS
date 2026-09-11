#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"preflight_gate_config.json"; CHANGE=M/"github_change_report.json"
GH=M/"github_read_health.json"; OUT=M/"preflight_gate_report.json"; HEALTH=M/"preflight_gate_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def run():
    c=load(CFG,{}); ch=load(CHANGE,{}); gh=load(GH,{})
    risk=int(ch.get("risk_score",100)); blockers=[]
    if risk>int(c.get("max_automatic_risk_score",34)): blockers.append("risk_score_above_automatic_threshold")
    if c.get("require_clean_worktree_for_deploy") and ch.get("changed_files"): blockers.append("working_tree_has_changes")
    if c.get("require_github_health") and not gh.get("healthy",False): blockers.append("github_connector_unhealthy")
    decision="ready_for_review" if not blockers else "blocked"
    out={"generated_at":datetime.now(timezone.utc).isoformat(),"decision":decision,
         "risk_score":risk,"blockers":blockers,
         "automatic_merge":False,"automatic_deploy":False,"automatic_spending":False}
    save(OUT,out);save(HEALTH,{"healthy":True,"last_checked_at":out["generated_at"],"decision":decision})
    return {"success":True,"status":"preflight_complete","report":out}
a=sys.argv[1] if len(sys.argv)>1 else "run"
r=run() if a=="run" else {"success":True,"status":"preflight_status","report":load(OUT,{})}
print(json.dumps(r,indent=2))
