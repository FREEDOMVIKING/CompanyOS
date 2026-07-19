#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
REG=MEM/"treasury_destination_registry.json"

def now():return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(REG.read_text())
    except:return {"destinations":[]}
def save(d):REG.write_text(json.dumps(d,indent=2))
def did(chain,address):return hashlib.sha256(f"{chain}|{address}".encode()).hexdigest()[:18]

a=sys.argv[1] if len(sys.argv)>1 else "list"
d=load()

if a=="register":
    chain,address,label=sys.argv[2],sys.argv[3],sys.argv[4]
    row={
      "destination_id":did(chain,address),
      "chain":chain,
      "address":address,
      "label":label,
      "enabled":True,
      "created_at":now()
    }
    d["destinations"]=[x for x in d.get("destinations",[]) if x.get("destination_id")!=row["destination_id"]]+[row]
    save(d);r={"success":True,"status":"destination_registered","destination":row}

elif a=="disable":
    ident=sys.argv[2];found=None
    for x in d.get("destinations",[]):
        if x.get("destination_id")==ident or x.get("address")==ident:
            x["enabled"]=False;x["updated_at"]=now();found=x
    save(d);r={"success":bool(found),"status":"destination_disabled","destination":found}

elif a=="enable":
    ident=sys.argv[2];found=None
    for x in d.get("destinations",[]):
        if x.get("destination_id")==ident or x.get("address")==ident:
            x["enabled"]=True;x["updated_at"]=now();found=x
    save(d);r={"success":bool(found),"status":"destination_enabled","destination":found}

else:
    r={"success":True,"status":"destination_registry","registry":d}

print(json.dumps(r,indent=2))
