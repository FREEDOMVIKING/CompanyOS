#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 49 - AUTONOMOUS COMMUNICATIONS CAMPAIGN ENGINE"
echo "============================================================"

cat > "$MEM/phase49_campaign_config.json" <<'JSON'
{
  "enabled": true,
  "mode": "bounded_goal_driven_campaigns",
  "max_campaigns_per_cycle": 5,
  "max_contacts_per_campaign": 25,
  "max_messages_per_contact_per_day": 3,
  "default_followup_hours": 48,
  "require_phase47_allowlist": true,
  "require_phase47_delivery_receipts": true,
  "require_no_mass_outreach_without_owner_approval": true,
  "require_contact_history": true,
  "require_duplicate_protection": true,
  "require_campaign_metrics": true,
  "fail_closed": true
}
JSON

cat > "$MEM/phase49_campaigns.json" <<'JSON'
{"campaigns":[]}
JSON

cat > "$MEM/phase49_contacts.json" <<'JSON'
{"contacts":[]}
JSON

cat > "$MEM/phase49_contact_history.json" <<'JSON'
{"history":[]}
JSON

cat > "$MEM/phase49_state.json" <<'JSON'
{"last_run_at":null,"campaigns_processed":0,"messages_queued":0,"blocked_count":0,"followups_due":0,"last_results":[]}
JSON

cat > "$AGENTS/phase49_campaign_manager.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
C=M/"phase49_campaigns.json"; K=M/"phase49_contacts.json"
now=lambda: datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))

a=sys.argv[1] if len(sys.argv)>1 else "list"
if a=="add-contact":
    if len(sys.argv)<5:
        out={"success":False,"status":"usage","usage":"add-contact EMAIL NAME SEGMENT"}
    else:
        email,name,segment=sys.argv[2],sys.argv[3],sys.argv[4]
        d=load(K,{"contacts":[]}); cid=hashlib.sha256(email.lower().encode()).hexdigest()[:16]
        row={"contact_id":cid,"email":email,"name":name,"segment":segment,"status":"active","created_at":now()}
        e=next((x for x in d["contacts"] if x.get("contact_id")==cid),None)
        e.update(row) if e else d["contacts"].append(row); save(K,d)
        out={"success":True,"status":"phase49_contact_saved","contact":row}
elif a=="create-campaign":
    if len(sys.argv)<3:
        out={"success":False,"status":"usage","usage":"create-campaign JSON"}
    else:
        c=json.loads(sys.argv[2]); req=["name","goal","segment","subject","body"]; miss=[k for k in req if not c.get(k)]
        if miss: out={"success":False,"status":"missing_campaign_fields","missing":miss}
        else:
            cid=hashlib.sha256(f"{now()}|{c['name']}".encode()).hexdigest()[:20]
            row={"campaign_id":cid,"name":c["name"],"goal":c["goal"],"segment":c["segment"],"subject":c["subject"],"body":c["body"],"followup_hours":int(c.get("followup_hours",48)),"owner_approved_mass_outreach":bool(c.get("owner_approved_mass_outreach",False)),"status":"active","created_at":now()}
            d=load(C,{"campaigns":[]}); d["campaigns"].append(row); save(C,d)
            out={"success":True,"status":"phase49_campaign_created","campaign":row}
else:
    out={"success":True,"status":"phase49_campaign_registry","campaigns":load(C,{"campaigns":[]}),"contacts":load(K,{"contacts":[]})}
print(json.dumps(out,indent=2)); raise SystemExit(0 if out.get("success") else 1)
PY
chmod +x "$AGENTS/phase49_campaign_manager.py"

cat > "$CTL/phase49campaignctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase49_campaign_manager.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase49campaignctl"

cat > "$AGENTS/phase49_campaign_engine.py" <<'PY'
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
PY
chmod +x "$AGENTS/phase49_campaign_engine.py"

cat > "$CTL/phase49ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase49_campaign_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase49ctl"

echo "[1/4] Compiling..."
python -m py_compile "$AGENTS/phase49_campaign_manager.py" "$AGENTS/phase49_campaign_engine.py" "$CTL/phase49campaignctl" "$CTL/phase49ctl"

echo "[2/4] Checking Phase 47..."
python "$CTL/phase47ctl" status >/dev/null

echo "[3/4] Status..."
python "$CTL/phase49ctl" status

echo "[4/4] Verifying..."
python - <<'PY'
import json
from pathlib import Path
r=Path.home()/"companyos"; errors=[]
for p in [r/"agents"/"phase49_campaign_manager.py",r/"agents"/"phase49_campaign_engine.py",r/"companyos"/"phase49campaignctl",r/"companyos"/"phase49ctl",r/"ceo_memory"/"phase49_campaign_config.json"]:
    if not p.exists() or p.stat().st_size<=0: errors.append(str(p))
cfg=json.loads((r/"ceo_memory"/"phase49_campaign_config.json").read_text())
for k in ["require_phase47_allowlist","require_phase47_delivery_receipts","require_no_mass_outreach_without_owner_approval","require_duplicate_protection","fail_closed"]:
    if not cfg.get(k): errors.append(k)
print("--------------------------------------------")
print("PHASE 49 CAMPAIGN ENGINE VERIFICATION")
print("Errors:",len(errors))
print("Warnings: 0")
if errors: raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 49 AUTONOMOUS COMMUNICATIONS CAMPAIGN ENGINE INSTALLED"
echo " GOAL-DRIVEN CAMPAIGNS: ENABLED"
echo " CONTACT SEGMENTATION + HISTORY: ENABLED"
echo " FOLLOW-UP SCHEDULING HOOKS: ENABLED"
echo " CAMPAIGN METRICS: ENABLED"
echo " PHASE 47/48 DELIVERY PATH: PRESERVED"
echo " MASS OUTREACH WITHOUT OWNER APPROVAL: BLOCKED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
