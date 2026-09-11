#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
SECURE="$HOME/.companyos_secure"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$SECURE" "$AGENTS" "$CTL" "$MEM"
chmod 700 "$SECURE"

echo "============================================================"
echo " PHASE 36 - MULTI-CHAIN LIVE EXECUTION ADAPTER SUITE"
echo "============================================================"

echo "[1/7] Installing secure signer dependencies..."
cd "$SECURE"

if [ ! -f package.json ]; then
cat > package.json <<'JSON'
{
  "name": "companyos-secure-signers",
  "version": "1.0.0",
  "private": true
}
JSON
fi

npm install @solana/web3.js @solana/spl-token bs58 ethers bitcoinjs-lib ecpair tiny-secp256k1

echo "[2/7] Installing secure multi-chain signer..."

cat > "$SECURE/multichain_signer.js" <<'JS'
#!/usr/bin/env node
"use strict";

const fs = require("fs");
const web3 = require("@solana/web3.js");
const spl = require("@solana/spl-token");
const bs58pkg = require("bs58");
const bs58 = bs58pkg.default || bs58pkg;
const { ethers } = require("ethers");
const bitcoin = require("bitcoinjs-lib");
const ecc = require("tiny-secp256k1");
const { ECPairFactory } = require("ecpair");
const ECPair = ECPairFactory(ecc);
bitcoin.initEccLib(ecc);

function fail(status, message, code=2) {
  console.log(JSON.stringify({success:false,status,message}));
  process.exit(code);
}
function readReq() {
  try { return JSON.parse(fs.readFileSync(0,"utf8")); }
  catch(e) { fail("invalid_request_json", `${e.name}: ${e.message}`); }
}
function solKeypair() {
  const raw=(process.env.SOLANA_PRIVATE_KEY_B58||"").trim();
  if(!raw) fail("missing_solana_private_key","SOLANA_PRIVATE_KEY_B58 missing");
  const decoded=bs58.decode(raw);
  if(decoded.length===64) return web3.Keypair.fromSecretKey(Uint8Array.from(decoded));
  if(decoded.length===32) return web3.Keypair.fromSeed(Uint8Array.from(decoded));
  fail("invalid_solana_private_key_length", String(decoded.length));
}

async function signSpl(r) {
  const kp=solKeypair();
  if(kp.publicKey.toBase58()!==r.source) fail("source_key_mismatch",`expected=${r.source} derived=${kp.publicKey.toBase58()}`);
  const mint=new web3.PublicKey(r.mint);
  const destOwner=new web3.PublicKey(r.destination);
  const sourceAta=new web3.PublicKey(r.source_token_account);
  const destAta=spl.getAssociatedTokenAddressSync(mint,destOwner,false,spl.TOKEN_PROGRAM_ID,spl.ASSOCIATED_TOKEN_PROGRAM_ID);
  const tx=new web3.Transaction({feePayer:kp.publicKey,recentBlockhash:r.recent_blockhash});
  if(r.create_destination_ata) {
    tx.add(spl.createAssociatedTokenAccountInstruction(
      kp.publicKey,destAta,destOwner,mint,spl.TOKEN_PROGRAM_ID,spl.ASSOCIATED_TOKEN_PROGRAM_ID
    ));
  }
  tx.add(spl.createTransferCheckedInstruction(
    sourceAta,mint,destAta,kp.publicKey,BigInt(r.amount_base_units),Number(r.decimals)
  ));
  tx.sign(kp);
  console.log(JSON.stringify({
    success:true,status:"signed",source:kp.publicKey.toBase58(),
    destination_token_account:destAta.toBase58(),
    signed_transaction_base64:Buffer.from(tx.serialize()).toString("base64")
  }));
}

async function signEvm(r) {
  const pk=(process.env.EVM_PRIVATE_KEY_HEX||"").trim();
  if(!pk) fail("missing_evm_private_key","EVM_PRIVATE_KEY_HEX missing");
  const wallet=new ethers.Wallet(pk);
  if(wallet.address.toLowerCase()!==String(r.source).toLowerCase())
    fail("source_key_mismatch",`expected=${r.source} derived=${wallet.address}`);
  const tx={
    to:r.to,
    nonce:BigInt(r.nonce),
    gasLimit:BigInt(r.gas_limit),
    chainId:BigInt(r.chain_id),
    value:BigInt(r.value_wei||0)
  };
  if(r.max_fee_per_gas) {
    tx.type=2;
    tx.maxFeePerGas=BigInt(r.max_fee_per_gas);
    tx.maxPriorityFeePerGas=BigInt(r.max_priority_fee_per_gas||0);
  } else {
    tx.gasPrice=BigInt(r.gas_price);
  }
  if(r.data) tx.data=r.data;
  const raw=await wallet.signTransaction(tx);
  console.log(JSON.stringify({success:true,status:"signed",source:wallet.address,signed_transaction_hex:raw}));
}

async function signBtc(r) {
  const wif=(process.env.BITCOIN_PRIVATE_KEY_WIF||"").trim();
  if(!wif) fail("missing_bitcoin_private_key","BITCOIN_PRIVATE_KEY_WIF missing");
  const network=bitcoin.networks.bitcoin;
  const key=ECPair.fromWIF(wif,network);
  const pay=bitcoin.payments.p2wpkh({pubkey:Buffer.from(key.publicKey),network});
  if(pay.address!==r.source) fail("source_key_mismatch",`expected=${r.source} derived=${pay.address}`);
  const psbt=new bitcoin.Psbt({network});
  for(const u of r.utxos) {
    psbt.addInput({
      hash:u.txid,
      index:Number(u.vout),
      witnessUtxo:{script:Buffer.from(pay.output),value:BigInt(u.value)}
    });
  }
  psbt.addOutput({address:r.destination,value:BigInt(r.send_sats)});
  if(BigInt(r.change_sats)>0n) psbt.addOutput({address:r.source,value:BigInt(r.change_sats)});
  for(let i=0;i<r.utxos.length;i++) psbt.signInput(i,key);
  psbt.finalizeAllInputs();
  const raw=psbt.extractTransaction().toHex();
  console.log(JSON.stringify({success:true,status:"signed",source:pay.address,signed_transaction_hex:raw}));
}

(async()=>{
  const r=readReq();
  try {
    if(r.action==="sign_spl_transfer") return await signSpl(r);
    if(r.action==="sign_evm_transaction") return await signEvm(r);
    if(r.action==="sign_btc_p2wpkh_transaction") return await signBtc(r);
    fail("unsupported_action",String(r.action));
  } catch(e) {
    fail("signing_failed",`${e.name}: ${e.message}`);
  }
})();
JS

chmod 700 "$SECURE/multichain_signer.js"

cat > "$SECURE/multichain_signer_wrapper.sh" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
source "$HOME/.companyos_secrets"
exec node "$HOME/.companyos_secure/multichain_signer.js"
SH
chmod 700 "$SECURE/multichain_signer_wrapper.sh"

cd "$ROOT"

echo "[3/7] Installing execution adapter engine..."

cat > "$MEM/phase36_execution_adapter_config.json" <<'JSON'
{
  "enabled": true,
  "single_transaction_auto_limit_usd": 15000,
  "daily_total_limit_usd": 20000,
  "signer_command_env": "MULTICHAIN_SIGNER_COMMAND",
  "routes": {
    "solana": ["SOL", "USDT-SPL", "USDC-SPL"],
    "evm": ["ETH", "USDT-ERC20", "USDC-ERC20"],
    "bitcoin": ["BTC"]
  },
  "token_contracts": {
    "evm": {
      "USDT-ERC20": {"contract":"0xdAC17F958D2ee523a2206206994597C13D831ec7","decimals":6},
      "USDC-ERC20": {"contract":"0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48","decimals":6}
    },
    "solana": {
      "USDT-SPL": {"mint":"Es9vMFrzaCERmJfrF4H2FYD4UQJk6de4M5GvQ7D6n5n","decimals":6},
      "USDC-SPL": {"mint":"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v","decimals":6}
    }
  },
  "bitcoin": {
    "fee_rate_sat_vb_default": 8,
    "dust_limit_sats": 546,
    "address_type": "p2wpkh"
  }
}
JSON

cat > "$AGENTS/multichain_execution_adapter.py" <<'PY'
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

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=execute(sys.argv[2]) if a=="execute" else {"success":True,"status":"multichain_adapter_ready",
 "signer_configured":bool(os.getenv("MULTICHAIN_SIGNER_COMMAND","").strip()),
 "evm_key_configured":bool(os.getenv("EVM_PRIVATE_KEY_HEX","").strip()),
 "btc_key_configured":bool(os.getenv("BITCOIN_PRIVATE_KEY_WIF","").strip())}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/multichain_execution_adapter.py"

cat > "$CTL/multichainexecutionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"multichain_execution_adapter.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/multichainexecutionctl"

echo "[4/7] Extending Phase 34 routes..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"phase34_autonomous_treasury_config.json"
d=json.loads(p.read_text())
d["supported_live_routes"]={
  "solana":["SOL","USDT-SPL","USDC-SPL"],
  "evm":["ETH","USDT-ERC20","USDC-ERC20"],
  "bitcoin":["BTC"]
}
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"supported_live_routes":d["supported_live_routes"]},indent=2))
PY

echo "[5/7] Extending Phase 34 execution routing..."
python - <<'PY'
from pathlib import Path
p=Path.home()/"companyos"/"agents"/"autonomous_treasury_orchestrator.py"
s=p.read_text()
old='''        if chain=="solana" and asset=="SOL":
            rc,r=execute_sol(pid)
        else:
            rc,r=1,{"success":False,"status":"executor_not_implemented"}
'''
new='''        if chain=="solana" and asset=="SOL":
            rc,r=execute_sol(pid)
        else:
            px=subprocess.run(
              [sys.executable,"companyos/multichainexecutionctl","execute",pid],
              cwd=ROOT,text=True,capture_output=True,timeout=300
            )
            rc=px.returncode
            try:r=json.loads(px.stdout)
            except:r={"success":False,"status":"invalid_multichain_executor_output","stdout":px.stdout[-2000:],"stderr":px.stderr[-1000:]}
'''
if old in s:
    p.write_text(s.replace(old,new,1))
    print("Phase34 router extended.")
elif "companyos/multichainexecutionctl" in s:
    print("Phase34 router already extended.")
else:
    raise SystemExit("ERROR: expected Phase34 routing block not found")
PY

echo "[6/7] Writing secure setup instructions..."
cat > "$SECURE/phase36_signer_setup.txt" <<'TXT'
Add to ~/.companyos_secrets:

export MULTICHAIN_SIGNER_COMMAND="$HOME/.companyos_secure/multichain_signer_wrapper.sh"

For EVM:
export EVM_PRIVATE_KEY_HEX='YOUR_DEDICATED_EVM_PRIVATE_KEY'

For native Bitcoin P2WPKH:
export BITCOIN_PRIVATE_KEY_WIF='YOUR_DEDICATED_BITCOIN_WIF'

Solana continues using:
export SOLANA_PRIVATE_KEY_B58='YOUR_DEDICATED_SOLANA_PRIVATE_KEY_BASE58'

Never commit these secrets or paste them into chat.
TXT

echo "[7/7] Compiling and verifying..."
python -m py_compile "$AGENTS/multichain_execution_adapter.py" "$CTL/multichainexecutionctl" "$AGENTS/autonomous_treasury_orchestrator.py"
node --check "$SECURE/multichain_signer.js"

source "$HOME/.companyos_secrets" 2>/dev/null || true
python "$CTL/multichainexecutionctl" status

python - <<'PY'
import json
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
 r/"agents"/"multichain_execution_adapter.py",
 r/"companyos"/"multichainexecutionctl",
 r/"ceo_memory"/"phase36_execution_adapter_config.json",
 Path.home()/".companyos_secure"/"multichain_signer.js",
 Path.home()/".companyos_secure"/"multichain_signer_wrapper.sh"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
cfg=json.loads((r/"ceo_memory"/"phase34_autonomous_treasury_config.json").read_text())
expected={
 "solana":["SOL","USDT-SPL","USDC-SPL"],
 "evm":["ETH","USDT-ERC20","USDC-ERC20"],
 "bitcoin":["BTC"]
}
if cfg.get("supported_live_routes")!=expected:errors.append("Phase34 live route map mismatch")
print("--------------------------------------------")
print("PHASE 36 MULTI-CHAIN ADAPTER VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 36 MULTI-CHAIN EXECUTION ADAPTER SUITE INSTALLED"
echo " SOL / SPL USDT / SPL USDC ADAPTERS: INSTALLED"
echo " ETH / ERC20 USDT / ERC20 USDC ADAPTERS: INSTALLED"
echo " NATIVE BTC P2WPKH ADAPTER: INSTALLED"
echo " POLICY / DESTINATION / LIMIT GATES: PRESERVED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "IMPORTANT:"
echo "  SOL remains live through the already-tested signer."
echo "  EVM and BTC cannot sign until their local dedicated keys are configured."
echo "  No private keys belong in GitHub."
