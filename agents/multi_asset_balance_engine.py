#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse, time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
REG=MEM/"treasury_wallet_registry.json"
CFG=MEM/"phase31_multi_asset_config.json"
OUT=MEM/"multi_asset_treasury_balances.json"
HEALTH=MEM/"phase31_rpc_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def env_expand(x):
    if isinstance(x,str) and x.startswith("${") and x.endswith("}"):
        return os.getenv(x[2:-1],"").strip()
    return x

def rpc_candidates(chain):
    cfg=load(CFG,{})
    vals=cfg.get("rpc_failover",{}).get(chain,[])
    out=[]
    for v in vals:
        v=env_expand(v)
        if v and v not in out: out.append(v)
    return out

def json_rpc(url,method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json","User-Agent":"CompanyOS/1.0"})
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.loads(r.read().decode())

def rest_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CompanyOS/1.0"})
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.loads(r.read().decode())

def first_ok(chain, fn):
    errs=[]
    for url in rpc_candidates(chain):
        try:return fn(url),url,None
        except Exception as e: errs.append(f"{url}: {type(e).__name__}: {e}")
    return None,None,errs

def sol_native(addr):
    def f(url):
        j=json_rpc(url,"getBalance",[addr,{"commitment":"confirmed"}])
        return float(j.get("result",{}).get("value",0))/1_000_000_000
    return first_ok("solana",f)

def sol_tokens(addr):
    contracts=load(CFG,{}).get("token_contracts",{}).get("solana",{})
    balances={}
    def f(url):
        j=json_rpc(url,"getTokenAccountsByOwner",[addr,{"programId":"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},{"encoding":"jsonParsed"}])
        vals=j.get("result",{}).get("value",[])
        bymint={}
        for x in vals:
            info=x.get("account",{}).get("data",{}).get("parsed",{}).get("info",{})
            mint=info.get("mint")
            amt=info.get("tokenAmount",{}).get("uiAmount")
            if mint: bymint[mint]=float(amt or 0)
        return bymint
    data,url,err=first_ok("solana",f)
    if data is None:return balances,url,err
    for symbol,mint in contracts.items():
        balances[symbol]=float(data.get(mint,0))
    return balances,url,None

def evm_native(addr):
    def f(url):
        j=json_rpc(url,"eth_getBalance",[addr,"latest"])
        return int(j.get("result","0x0"),16)/1e18
    return first_ok("evm",f)

def pad_addr(addr):
    return addr.lower().replace("0x","").rjust(64,"0")
def evm_token_balance(addr,contract,decimals):
    data="0x70a08231"+pad_addr(addr)
    def f(url):
        j=json_rpc(url,"eth_call",[{"to":contract,"data":data},"latest"])
        return int(j.get("result","0x0"),16)/(10**decimals)
    return first_ok("evm",f)

def btc_balance(addr):
    def f(base):
        base=base.rstrip("/")
        if "blockstream.info" in base or "mempool.space" in base:
            j=rest_json(f"{base}/address/{urllib.parse.quote(addr)}")
            cs=j.get("chain_stats",{}); ms=j.get("mempool_stats",{})
            funded=int(cs.get("funded_txo_sum",0))+int(ms.get("funded_txo_sum",0))
            spent=int(cs.get("spent_txo_sum",0))+int(ms.get("spent_txo_sum",0))
            return (funded-spent)/1e8
        raise RuntimeError("Unsupported BTC endpoint type")
    return first_ok("bitcoin",f)

rows=[]; health={}
cfg=load(CFG,{})
for w in load(REG,{}).get("wallets",[]):
    chain=w.get("chain");addr=w.get("address")
    row={"wallet_id":w.get("wallet_id"),"chain":chain,"address":addr,"checked_at":now(),"assets":{}}
    if chain=="solana":
        bal,url,err=sol_native(addr)
        if bal is not None:
            row["assets"]["SOL"]=bal
            toks,turl,terr=sol_tokens(addr)
            row["assets"].update(toks)
            row["status"]="ok";row["rpc_used"]=turl or url
        else:
            row["status"]="error";row["errors"]=err
    elif chain=="evm":
        bal,url,err=evm_native(addr)
        if bal is not None:
            row["assets"]["ETH"]=bal
            for sym,contract in cfg.get("token_contracts",{}).get("evm",{}).items():
                dec=6
                tb,turl,terr=evm_token_balance(addr,contract,dec)
                row["assets"][sym]=tb if tb is not None else None
            row["status"]="ok";row["rpc_used"]=url
        else:
            row["status"]="error";row["errors"]=err
    elif chain=="bitcoin":
        bal,url,err=btc_balance(addr)
        if bal is not None:
            row["assets"]["BTC"]=bal;row["status"]="ok";row["rpc_used"]=url
        else:
            row["status"]="error";row["errors"]=err
    rows.append(row)
    health[chain]={"healthy":row.get("status")=="ok","rpc_used":row.get("rpc_used"),"checked_at":now()}

payload={"generated_at":now(),"wallet_count":len(rows),"balances":rows}
OUT.write_text(json.dumps(payload,indent=2))
HEALTH.write_text(json.dumps({"generated_at":now(),"chains":health,"healthy":all(x.get("healthy") for x in health.values()) if health else False},indent=2))
print(json.dumps({"success":True,"status":"multi_asset_balance_complete","report":payload},indent=2))
