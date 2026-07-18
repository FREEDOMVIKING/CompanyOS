#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"opportunity_translation_config.json"
QUEUE=MEM/"opportunity_activation_queue.json"
ELIGIBILITY=MEM/"execution_eligibility_report.json"
STATE=MEM/"opportunity_translation_state.json"
REPORT=MEM/"opportunity_translation_report.json"
HEALTH=MEM/"opportunity_translation_health.json"
ACTION_QUEUE=MEM/"opportunity_action_queue.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)

def translate_text(item:dict[str,Any]):
    title=item.get("title") or "Untitled opportunity"
    recommendation=item.get("recommendation") or ""
    category=item.get("category") or "internal_read_only"
    out=[{
        "action_id":f"{item.get('id') or 'opp'}-analyze",
        "title":f"Analyze opportunity: {title}",
        "category":"internal_read_only",
        "priority":item.get("alignment_score",50),
        "instruction":recommendation or f"Analyze the opportunity '{title}' and produce the next best internal step."
    }]
    if category in {"internal_reversible","internal_read_only","external_read_only"}:
        out.append({
            "action_id":f"{item.get('id') or 'opp'}-prepare",
            "title":f"Prepare next action for: {title}",
            "category":"internal_reversible",
            "priority":max(1,float(item.get("alignment_score",50))-5),
            "instruction":f"Prepare a reversible internal action plan for '{title}' without contacting customers, publishing, spending, deploying, or changing external systems."
        })
    return out

def translate():
    cfg=load(CFG,{})
    queue=load(QUEUE,{})
    eligibility=load(ELIGIBILITY,{})
    matrix=eligibility.get("eligibility",{})
    maximum=int(cfg.get("maximum_actions",10))
    translated=[]; blocked=[]
    for candidate in queue.get("candidates",[]):
        for action in translate_text(candidate):
            category=action.get("category",cfg.get("default_category","internal_read_only"))
            if not bool(matrix.get(category,False)):
                blocked.append({**action,"reason":"category_not_eligible"})
                continue
            translated.append(action)
            if len(translated)>=maximum: break
        if len(translated)>=maximum: break
    save(ACTION_QUEUE,{"generated_at":now(),"actions":translated})
    report={"generated_at":now(),"translated_count":len(translated),"blocked_count":len(blocked),
            "actions":translated,"blocked":blocked,
            "automatic_external_write":False,"automatic_customer_contact":False,
            "automatic_publication":False,"automatic_spending":False,
            "automatic_code_changes":False,"automatic_merge":False,
            "automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_translated_at":now(),"translated_count":len(translated),"blocked_count":len(blocked)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"translated_count":len(translated)})
    return {"success":True,"status":"opportunity_translation_complete","report":report}

def status():
    return {"success":True,"status":"opportunity_translation_status","state":load(STATE,{}),
            "health":load(HEALTH,{}),"report":load(REPORT,{}),"queue":load(ACTION_QUEUE,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=translate() if a=="translate" else status() if a=="status" else {"success":False,"allowed":["translate","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
