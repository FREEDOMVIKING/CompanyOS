#!/usr/bin/env python3
import json,os,shlex,subprocess,sys,urllib.request,urllib.parse
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"phase36_execution_adapter_config.json"
PROPS=MEM/"transaction_proposals.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def rpc(url,m,p):
    req=urllib.request.Request(url,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=25) as r:j=json.loads(r.read().decode())
    if j.get("error"):raise RuntimeError(j["error"])
    return j.get("result")
def rest(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"CompanyOS/1.0"}),timeout=25) as r:return json.loads(r.read().decode())
def signer(payload):
    cmd=os.getenv("MULTICHAIN_SIGNER_COMMAND","").strip()
    if not cmd:raise RuntimeError("MULTICHAIN_SIGNER_COMMAND missing")
    p=subprocess.run(shlex.split(cmd),input=json.dumps(payload),text=True,capture_output=True,timeout=180)
    if p.returncode:return {"success":False,"status":"signer_failed","stderr":p.stderr[-1000:],"stdout":p.stdout[-1000:]}
    return json.loads(p.stdout)
def proposal(pid):
    return next((x for x in load(PROPS,{"proposals":[]}).get("proposals",[]) if x.get("proposal_id")==pid),None)

def spl(p):
    url=os.getenv("SOLANA_RPC_URL","").strip();cfg=load(CFG,{})
    meta=cfg["token_contracts"]["solana"][p["asset"]];mint=meta["mint"];dec=meta["decimals"]
    accounts=rpc(url,"getTokenAccountsByOwner",[p["source"],{"mint":mint},{"encoding":"jsonParsed"}]).get("value",[])
    if not accounts:return {"success":False,"status":"source_token_account_missing"}
    source_ata=accounts[0]["pubkey"]
    raw=int(round(float(p["amount_native"])*(10**dec)))
    bh=rpc(url,"getLatestBlockhash",[{"commitment":"confirmed"}])["value"]["blockhash"]
    dest_accounts=rpc(url,"getTokenAccountsByOwner",[p["destination"],{"mint":mint},{"encoding":"jsonParsed"}]).get("value",[])
    s=signer({"action":"sign_spl_transfer","source":p["source"],"destination":p["destination"],"mint":mint,
              "source_token_account":source_ata,"amount_base_units":str(raw),"decimals":dec,
              "recent_blockhash":bh,"create_destination_ata":not bool(dest_accounts)})
    if not s.get("success"):return s
    b64=s["signed_transaction_base64"]
    sim=rpc(url,"simulateTransaction",[b64,{"encoding":"base64","sigVerify":True,"commitment":"confirmed"}])
    if sim["value"]["err"] is not None:return {"success":False,"status":"preflight_failed","detail":sim["value"]["err"]}
    txid=rpc(url,"sendTransaction",[b64,{"encoding":"base64","skipPreflight":False,"preflightCommitment":"confirmed","maxRetries":3}])
    return {"success":True,"status":"broadcast","txid":txid}

def evm(p):
    url=os.getenv("EVM_RPC_URL","").strip() or "https://ethereum.publicnode.com";cfg=load(CFG,{})
    chain=int(rpc(url,"eth_chainId",[]),16)
    nonce=int(rpc(url,"eth_getTransactionCount",[p["source"],"pending"]),16)
    try:priority=int(rpc(url,"eth_maxPriorityFeePerGas",[]),16)
    except:priority=1_500_000_000
    block=rpc(url,"eth_getBlockByNumber",["latest",False]);base=int(block.get("baseFeePerGas","0x0"),16)
    maxfee=base*2+priority
    to=p["destination"];value=0;data="0x"
    if p["asset"]=="ETH":
        value=int(round(float(p["amount_native"])*1e18))
    else:
        m=cfg["token_contracts"]["evm"][p["asset"]];to=m["contract"]
        selector="a9059cbb";addr=p["destination"].lower().replace("0x","").rjust(64,"0")
        amt=hex(int(round(float(p["amount_native"])*(10**m["decimals"]))))[2:].rjust(64,"0")
        data="0x"+selector+addr+amt
    call={"from":p["source"],"to":to,"value":hex(value),"data":data}
    gas=int(rpc(url,"eth_estimateGas",[call]),16)
    s=signer({"action":"sign_evm_transaction","source":p["source"],"to":to,"value_wei":str(value),"data":data,
              "nonce":str(nonce),"gas_limit":str(gas),"chain_id":str(chain),
              "max_fee_per_gas":str(maxfee),"max_priority_fee_per_gas":str(priority)})
    if not s.get("success"):return s
    txid=rpc(url,"eth_sendRawTransaction",[s["signed_transaction_hex"]])
    return {"success":True,"status":"broadcast","txid":txid}

def btc(p):
    base=os.getenv("BITCOIN_RPC_URL","").strip() or "https://blockstream.info/api"
    if not ("blockstream.info" in base or "mempool.space" in base):base="https://blockstream.info/api"
    base=base.rstrip("/")
    utxos=rest(f"{base}/address/{urllib.parse.quote(p['source'])}/utxo")
    need=int(round(float(p["amount_native"])*1e8));selected=[];total=0
    for u in sorted(utxos,key=lambda x:x["value"],reverse=True):
        selected.append(u);total+=int(u["value"])
        if total>=need+2000:break
    if total<need:return {"success":False,"status":"insufficient_btc_balance"}
    fee_rate=8;vbytes=10+68*len(selected)+31*2;fee=fee_rate*vbytes;change=total-need-fee
    if change<0:return {"success":False,"status":"insufficient_for_fee"}
    if change<546:fee+=change;change=0
    s=signer({"action":"sign_btc_p2wpkh_transaction","source":p["source"],"destination":p["destination"],
              "send_sats":str(need),"change_sats":str(change),"utxos":selected})
    if not s.get("success"):return s
    raw=s["signed_transaction_hex"]
    req=urllib.request.Request(f"{base}/tx",data=raw.encode(),method="POST",headers={"Content-Type":"text/plain"})
    with urllib.request.urlopen(req,timeout=30) as r:txid=r.read().decode().strip()
    return {"success":True,"status":"broadcast","txid":txid,"fee_sats":fee}

def execute(pid):
    p=proposal(pid)
    if not p:return {"success":False,"status":"proposal_not_found"}
    if p.get("status")!="ready_for_signing" or not p.get("signing_authorized"):return {"success":False,"status":"not_authorized"}
    if p["chain"]=="solana" and p["asset"]=="SOL":return {"success":False,"status":"use_existing_solana_sol_executor"}
    if p["chain"]=="solana":return spl(p)
    if p["chain"]=="evm":return evm(p)
    if p["chain"]=="bitcoin":return btc(p)
    return {"success":False,"status":"unsupported_route"}

def main():
    a=sys.argv[1] if len(sys.argv)>1 else "status"
    r=execute(sys.argv[2]) if a=="execute" else {
        "success":True,
        "status":"multichain_adapter_ready",
        "signer_configured":bool(os.getenv("MULTICHAIN_SIGNER_COMMAND","").strip()),
        "evm_key_configured":bool(os.getenv("EVM_PRIVATE_KEY_HEX","").strip()),
        "btc_key_configured":bool(os.getenv("BITCOIN_PRIVATE_KEY_WIF","").strip())
    }
    print(json.dumps(r,indent=2))
    return 0 if r.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
