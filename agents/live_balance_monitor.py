#!/usr/bin/env python3
import json, os, urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
REG=MEM/"treasury_wallet_registry.json"
CFG=MEM/"phase30_treasury_monitor_config.json"
OUT=MEM/"live_treasury_balances.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def rpc(url,method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=15) as r:return json.loads(r.read().decode())
def sol_balance(url,address):
    j=rpc(url,"getBalance",[address,{"commitment":"confirmed"}])
    return float(j.get("result",{}).get("value",0))/1_000_000_000
def evm_balance(url,address):
    j=rpc(url,"eth_getBalance",[address,"latest"])
    return int(j.get("result","0x0"),16)/1e18

cfg=load(CFG,{})
rows=[]
for w in load(REG,{}).get("wallets",[]):
    chain=w.get("chain");address=w.get("address")
    env=cfg.get("chains",{}).get(chain,{}).get("rpc_url_env")
    url=os.getenv(env or "","").strip()
    row={"wallet_id":w.get("wallet_id"),"chain":chain,"address":address,"checked_at":now()}
    if not url:
        row.update({"status":"rpc_not_configured","balance":None})
    else:
        try:
            if chain=="solana":
                row.update({"status":"ok","native_asset":"SOL","balance":sol_balance(url,address)})
            elif chain=="evm":
                row.update({"status":"ok","native_asset":"ETH","balance":evm_balance(url,address)})
            elif chain=="bitcoin":
                row.update({"status":"rpc_configured_adapter_pending","native_asset":"BTC","balance":None})
            else:
                row.update({"status":"unsupported_chain","balance":None})
        except Exception as e:
            row.update({"status":"error","error":f"{type(e).__name__}: {e}","balance":None})
    rows.append(row)

payload={"generated_at":now(),"wallet_count":len(rows),"balances":rows}
OUT.write_text(json.dumps(payload,indent=2))
print(json.dumps({"success":True,"status":"live_balance_monitor_complete","report":payload},indent=2))
