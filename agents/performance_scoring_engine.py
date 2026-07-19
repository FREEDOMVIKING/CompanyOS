#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"business_performance_scorecard.json"; STATE=MEM/"business_performance_state.json"; HEALTH=MEM/"business_performance_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def score():
    autonomy=load("autonomy_core_health.json",{})
    resource=load("resource_monitor_report.json",{})
    portfolio=load("portfolio_performance_report.json",{})
    outcomes=load("outcome_tracker_report.json",{})
    reliability=load("reliability_health.json",{})

    metrics={
      "autonomy_health":100 if autonomy.get("healthy",False) else 50,
      "reliability":float(reliability.get("reliability_score",80) or 80),
      "portfolio_activity":min(100,float(portfolio.get("priority_count",0) or 0)*20+40),
      "outcome_visibility":80 if outcomes else 40,
      "resource_health":100 if resource.get("status") in ("healthy","ok",None) else 60
    }
    overall=round(sum(metrics.values())/len(metrics),2)
    payload={"generated_at":now(),"overall_score":overall,"metrics":metrics,
      "status":"healthy" if overall>=75 else "watch" if overall>=55 else "attention"}
    save(OUT,payload);save(STATE,{"last_scored_at":now(),"overall_score":overall})
    save(HEALTH,{"healthy":overall>=55,"last_checked_at":now(),"overall_score":overall})
    return {"success":True,"status":"business_performance_scoring_complete","scorecard":payload}

def status():
    return {"success":True,"status":"business_performance_status",
      "state":load("business_performance_state.json",{}),"health":load("business_performance_health.json",{}),
      "scorecard":load("business_performance_scorecard.json",{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=score() if a=="score" else status() if a=="status" else {"success":False,"allowed":["score","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
