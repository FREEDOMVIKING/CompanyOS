#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
REG=MEM/"treasury_wallet_registry.json"

def now():return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(REG.read_text())
    except:return {"wallets":[]}
def save(d):REG.write_text(json.dumps(d,indent=2))
def wid(chain,address):return hashlib.sha256(f"{chain}|{address}".encode()).hexdigest()[:18]

a=sys.argv[1] if len(sys.argv)>1 else "list"
d=load()
if a=="register":
    chain,address,label=sys.argv[2],sys.argv[3],sys.argv[4]
    item={
      "wallet_id":wid(chain,address),
      "chain":chain,
      "address":address,
      "label":label,
      "enabled":True,
      "created_at":now()
    }
    d["wallets"]=[x for x in d.get("wallets",[]) if x.get("wallet_id")!=item["wallet_id"]]+[item]
    save(d);r={"success":True,"status":"treasury_wallet_registered","wallet":item}
else:
    r={"success":True,"status":"treasury_wallet_registry","registry":d}
print(json.dumps(r,indent=2))
