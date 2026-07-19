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
