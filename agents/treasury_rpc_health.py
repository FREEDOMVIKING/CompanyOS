#!/usr/bin/env python3
import json, os, urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase30_treasury_monitor_config.json"
OUT=MEM/"treasury_rpc_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def probe(url, chain):
    if not url:
        return {"configured":False,"reachable":False}
    try:
        if chain=="solana":
            body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getHealth"}).encode()
        elif chain=="evm":
            body=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}).encode()
        else:
            return {"configured":True,"reachable":True,"mode":"url_present"}
        req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=10) as r:
            return {"configured":True,"reachable":True,"http_status":getattr(r,"status",200)}
    except Exception as e:
        return {"configured":True,"reachable":False,"error":f"{type(e).__name__}: {e}"}

cfg=load(CFG,{})
chains={}
for chain,cc in cfg.get("chains",{}).items():
    env=cc.get("rpc_url_env")
    chains[chain]=probe(os.getenv(env,"").strip(),chain)

payload={"generated_at":now(),"chains":chains,"healthy":any(v.get("reachable") for v in chains.values())}
OUT.write_text(json.dumps(payload,indent=2))
print(json.dumps({"success":True,"status":"treasury_rpc_health_complete","report":payload},indent=2))
