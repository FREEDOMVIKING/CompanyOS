#!/usr/bin/env python3
import json,subprocess,sys,hashlib
from datetime import datetime,timezone,timedelta
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"phase49_campaign_config.json"; CAM=M/"phase49_campaigns.json"; CON=M/"phase49_contacts.json"; HIS=M/"phase49_contact_history.json"; STA=M/"phase49_state.json"; REP=M/"phase49_report.json"

def now(): return datetime.now(timezone.utc)
def iso(): return now().isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d): p.write_text(json.dumps(d,indent=2))
def run(args):
    p=subprocess.run(args,cwd=R,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stderr":p.stderr[-1000:]}
    return p.returncode,r
def allowed(email):
    rc,r=run([sys.executable,"companyos/phase47allowlistctl","list"])
    return rc==0 and any(x.get("enabled") and x.get("channel")=="email" and x.get("recipient")==email for x in (r.get("registry") or {}).get("recipients",[]))
def sent_today(h,email):
    cut=now()-timedelta(hours=24); n=0
    for x in h["history"]:
        if x.get("email")!=email or not x.get("success"): continue
        try:
            if datetime.fromisoformat(x["created_at"])>=cut:n+=1
        except: pass
    return n
def render(t,c): return str(t).replace("{{name}}",c.get("name","")).replace("{{email}}",c.get("email",""))

def cycle():
    cfg=load(CFG,{})
    cams=load(CAM,{"campaigns":[]}); cons=load(CON,{"contacts":[]}); hist=load(HIS,{"history":[]})
    results=[]; sent=blocked=follow=0
    active=[c for c in cams["campaigns"] if c.get("status")=="active"]

    for c in active[:int(cfg.get("max_campaigns_per_cycle",5))]:
        matches=[x for x in cons["contacts"] if x.get("status")=="active" and x.get("segment")==c.get("segment")]
        if len(matches)>1 and cfg.get("require_no_mass_outreach_without_owner_approval") and not c.get("owner_approved_mass_outreach"):
            results.append({"campaign_id":c["campaign_id"],"success":False,"status":"mass_outreach_requires_owner_approval","contact_count":len(matches)}); blocked+=len(matches); continue
        for ct in matches[:int(cfg.get("max_contacts_per_campaign",25))]:
            email=ct["email"]
            if not allowed(email):
                results.append({"campaign_id":c["campaign_id"],"email":email,"success":False,"status":"recipient_not_allowlisted"}); blocked+=1; continue
            if sent_today(hist,email)>=int(cfg.get("max_messages_per_contact_per_day",3)):
                results.append({"campaign_id":c["campaign_id"],"email":email,"success":False,"status":"daily_contact_limit_reached"}); blocked+=1; continue
            subject=render(c["subject"],ct); body=render(c["body"],ct)
            key=hashlib.sha256(f"{c['campaign_id']}|{email}|{subject}|{body}".encode()).hexdigest()
            if any(x.get("message_key")==key and x.get("success") for x in hist["history"]):
                results.append({"campaign_id":c["campaign_id"],"email":email,"success":True,"status":"duplicate_skipped"}); continue
            payload={"channel":"email","recipient":email,"subject":subject,"body":body,"metadata":{"campaign_id":c["campaign_id"],"contact_id":ct["contact_id"],"goal":c["goal"]}}
            rc,r=run([sys.executable,"companyos/phase47ctl","send",json.dumps(payload)])
            ok=rc==0 and bool(r.get("success"))
            hist["history"].append({"created_at":iso(),"campaign_id":c["campaign_id"],"contact_id":ct["contact_id"],"email":email,"message_key":key,"success":ok,"status":r.get("status"),"receipt":r.get("receipt")})
            results.append({"campaign_id":c["campaign_id"],"email":email,"success":ok,"status":r.get("status")})
            if ok: sent+=1; follow+=1
            else: blocked+=1

    save(HIS,hist)
    state={"last_run_at":iso(),"campaigns_processed":len(active),"messages_queued":sent,"blocked_count":blocked,"followups_due":follow,"last_results":results[-20:]}
    save(STA,state)
    report={"generated_at":iso(),"campaign_count":len(active),"messages_sent":sent,"blocked_count":blocked,"followups_scheduled":follow,"results":results}
    save(REP,report)
    return {"success":True,"status":"phase49_campaign_cycle_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "status"
out=cycle() if a=="run" else {"success":True,"status":"phase49_campaign_status","config":load(CFG,{}),"state":load(STA,{}),"campaigns":load(CAM,{"campaigns":[]}),"contacts":load(CON,{"contacts":[]})}
print(json.dumps(out,indent=2))
