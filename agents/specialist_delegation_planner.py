#!/usr/bin/env python3
import json,sys,re
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_delegation_config.json"
PLAN=MEM/"internal_resource_plan.json"
STATE=MEM/"specialist_delegation_state.json"
REPORT=MEM/"specialist_delegation_report.json"
HEALTH=MEM/"specialist_delegation_health.json"
OUT=MEM/"specialist_assignment_plan.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def choose(title,category):
    text=f"{title} {category}".lower()
    rules=[
      ("research",r"research|market|discover|analysis|investigat"),
      ("marketing",r"market|growth|audience|brand|content|lead"),
      ("finance",r"finance|revenue|pricing|margin|capital|cost"),
      ("engineering",r"software|code|app|api|platform|automation|technical"),
      ("product",r"product|customer|feature|offer"),
      ("operations",r"operation|process|workflow|service"),
    ]
    for role,pat in rules:
        if re.search(pat,text):return role
    return "strategy"

def delegate():
    cfg=load(CFG,{})
    allocations=load(PLAN,{}).get("allocations",[])
    specialists=cfg.get("specialists",{})
    maximum=int(cfg.get("maximum_assignments",10))
    assignments=[]
    for row in allocations[:maximum]:
        role=choose(row.get("title",""),row.get("category",""))
        assignments.append({
          "assignment_id":f"{row.get('id') or 'opportunity'}-{role}",
          "opportunity_id":row.get("id"),"title":row.get("title"),
          "specialist_role":role,"specialist":specialists.get(role,f"{role}_agent"),
          "attention_units":row.get("attention_units",0),
          "status":"planned_internal_assignment",
          "instruction":f"Analyze and advance the internal planning work for '{row.get('title')}' within current safety and execution eligibility limits."
        })
    out={"generated_at":now(),"assignment_count":len(assignments),"assignments":assignments}
    save(OUT,out)
    report={"generated_at":now(),"assignment_count":len(assignments),"assignments":assignments,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_planned_at":now(),"assignment_count":len(assignments)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"assignment_count":len(assignments)})
    return {"success":True,"status":"specialist_delegation_plan_complete","report":report}

def status():
    return {"success":True,"status":"specialist_delegation_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"plan":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=delegate() if a=="plan" else status() if a=="status" else {"success":False,"allowed":["plan","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
