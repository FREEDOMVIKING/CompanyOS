#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
CFG=MEM/"connector_registry_config.json"
REG=MEM/"connector_registry.json"
HEALTH=MEM/"connector_registry_health.json"
GATEWAY_CFG=MEM/"execution_gateway_config.json"

DEFAULT_CONNECTORS=[
 {"id":"github","name":"GitHub","type":"code_repository","read":True,"write":True,"enabled":True},
 {"id":"email","name":"Email","type":"communications","read":True,"write":False,"enabled":False},
 {"id":"calendar","name":"Calendar","type":"scheduling","read":True,"write":False,"enabled":False},
 {"id":"crm","name":"CRM","type":"business_data","read":True,"write":False,"enabled":True},
 {"id":"accounting","name":"Accounting","type":"finance_data","read":True,"write":False,"enabled":True},
 {"id":"market-data","name":"Market Data","type":"external_data","read":True,"write":False,"enabled":False}
]

def now(): return datetime.now(timezone.utc).isoformat()
def load(p:Path,d:Any)->Any:
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return d
def save(p:Path,d:Any)->None:
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2),encoding="utf-8")
    t.replace(p)

def discover():
    cfg=load(CFG,{})
    gateway=load(GATEWAY_CFG,{})
    store=load(REG,{"schema_version":1,"connectors":[]})
    existing={x.get("id"):x for x in store.get("connectors",[])}

    for item in DEFAULT_CONNECTORS:
        current=existing.get(item["id"],{})
        merged={**item,**current}
        merged["last_discovered_at"]=now()
        existing[item["id"]]=merged

    connectors=list(existing.values())
    save(REG,{"schema_version":1,"generated_at":now(),"connectors":connectors})

    enabled=sum(1 for x in connectors if x.get("enabled"))
    writable=sum(1 for x in connectors if x.get("enabled") and x.get("write"))

    save(HEALTH,{
      "healthy":True,
      "last_discovered_at":now(),
      "connector_count":len(connectors),
      "enabled_count":enabled,
      "write_capable_count":writable,
      "gateway_present":bool(gateway)
    })

    return {"success":True,"status":"connector_discovery_complete",
            "connectors":connectors}

def status():
    return {"success":True,"status":"connector_registry_status",
            "config":load(CFG,{}),"registry":load(REG,{}),
            "health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=discover() if a=="discover" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["discover","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
