#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"phase47_recipient_allowlist.json"

def now():return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(P.read_text())
    except:return {"recipients":[]}
def save(d):P.write_text(json.dumps(d,indent=2))

a=sys.argv[1] if len(sys.argv)>1 else "list"

if a=="add":
    if len(sys.argv)<4:
        out={"success":False,"status":"usage","usage":"add CHANNEL RECIPIENT [LABEL]"}
    else:
        channel=sys.argv[2]
        recipient=sys.argv[3]
        label=sys.argv[4] if len(sys.argv)>4 else recipient
        d=load()
        existing=next((r for r in d.get("recipients",[]) if r.get("channel")==channel and r.get("recipient")==recipient),None)
        if existing:
            existing["enabled"]=True
            existing["label"]=label
        else:
            d.setdefault("recipients",[]).append({
              "recipient_id":hashlib.sha256(f"{channel}|{recipient}".encode()).hexdigest()[:16],
              "channel":channel,
              "recipient":recipient,
              "label":label,
              "enabled":True,
              "created_at":now()
            })
        save(d)
        out={"success":True,"status":"recipient_allowlisted","channel":channel,"recipient":recipient}
elif a=="remove":
    if len(sys.argv)<4:
        out={"success":False,"status":"usage","usage":"remove CHANNEL RECIPIENT"}
    else:
        d=load()
        for r in d.get("recipients",[]):
            if r.get("channel")==sys.argv[2] and r.get("recipient")==sys.argv[3]:
                r["enabled"]=False
        save(d)
        out={"success":True,"status":"recipient_disabled"}
else:
    out={"success":True,"status":"phase47_allowlist","registry":load()}

print(json.dumps(out,indent=2))
raise SystemExit(0 if out.get("success") else 1)
