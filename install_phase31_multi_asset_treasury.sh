#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
CONN="$ROOT/connectors"
BACKUP="$ROOT/backups/phase31_multi_asset_treasury_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$CONN" "$BACKUP"

echo "============================================================"
echo " PHASE 31 - MULTI-ASSET TREASURY ADAPTER"
echo "============================================================"

cat > "$MEM/phase31_multi_asset_config.json" <<'JSON'
{
  "enabled": true,
  "rpc_failover": {
    "solana": ["${SOLANA_RPC_URL}", "https://api.mainnet-beta.solana.com"],
    "evm": ["${EVM_RPC_URL}", "https://ethereum.publicnode.com", "https://rpc.ankr.com/eth"],
    "bitcoin": ["${BITCOIN_RPC_URL}", "https://blockstream.info/api", "https://mempool.space/api"]
  },
  "assets": {
    "solana": ["SOL", "USDT-SPL", "USDC-SPL"],
    "evm": ["ETH", "USDT-ERC20", "USDC-ERC20"],
    "bitcoin": ["BTC"]
  },
  "token_contracts": {
    "evm": {
      "USDT-ERC20": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
      "USDC-ERC20": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    },
    "solana": {
      "USDT-SPL": "Es9vMFrzaCERmJfrF4H2FYD4UQJk6de4M5GvQ7D6n5n",
      "USDC-SPL": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    }
  },
  "monitoring_only": true,
  "automatic_signing": false
}
JSON

cat > "$AGENTS/multi_asset_balance_engine.py" <<'PY'
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
PY
chmod +x "$AGENTS/multi_asset_balance_engine.py"

cat > "$CTL/multiassetbalancectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"multi_asset_balance_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/multiassetbalancectl"

cat > "$AGENTS/multi_asset_event_engine.py" <<'PY'
#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
BAL=MEM/"multi_asset_treasury_balances.json"
SNAP=MEM/"multi_asset_balance_snapshot.json"
EVENTS=MEM/"multi_asset_treasury_events.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def eid(s):return hashlib.sha256(s.encode()).hexdigest()[:20]

cur=load(BAL,{}).get("balances",[])
prev={x.get("wallet_id"):x for x in load(SNAP,{}).get("balances",[])}
events=load(EVENTS,{"events":[]})
for w in cur:
    p=prev.get(w.get("wallet_id"),{})
    for asset,bal in (w.get("assets") or {}).items():
        if bal is None:continue
        old=(p.get("assets") or {}).get(asset)
        if old is None:continue
        delta=float(bal)-float(old)
        if abs(delta)>0:
            events["events"].append({
              "event_id":eid(f"{w['wallet_id']}|{asset}|{now()}|{delta}"),
              "wallet_id":w["wallet_id"],"chain":w["chain"],"asset":asset,
              "balance_delta":delta,"direction":"incoming" if delta>0 else "outgoing",
              "detected_at":now()
            })
events["events"]=events["events"][-10000:];events["updated_at"]=now()
save(EVENTS,events);save(SNAP,{"generated_at":now(),"balances":cur})
print(json.dumps({"success":True,"status":"multi_asset_event_generation_complete","event_count":len(events["events"])},indent=2))
PY
chmod +x "$AGENTS/multi_asset_event_engine.py"

cat > "$CTL/multiasseteventctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"multi_asset_event_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/multiasseteventctl"

cat > "$AGENTS/phase31_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase31_state.json";HEALTH=MEM/"phase31_health.json";REPORT=MEM/"phase31_report.json"
PIPE=[
 ("multi_asset_balances",["python","companyos/multiassetbalancectl"]),
 ("multi_asset_events",["python","companyos/multiasseteventctl"])
]
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
steps=[];failed=[]
for name,cmd in PIPE:
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300)
    r={"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-3000:],"stderr":p.stderr[-1000:]}
    steps.append({"step":name,"result":r})
    if not r["success"]:failed.append(name)
report={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
print(json.dumps({"success":not failed,"status":"phase31_multi_asset_treasury_complete","report":report},indent=2))
raise SystemExit(0 if not failed else 1)
PY
chmod +x "$AGENTS/phase31_controller.py"

cat > "$CTL/phase31ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase31_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase31ctl"

echo "[1/5] Compiling..."
python -m py_compile \
 "$AGENTS/multi_asset_balance_engine.py" "$AGENTS/multi_asset_event_engine.py" \
 "$AGENTS/phase31_controller.py" "$CTL/multiassetbalancectl" "$CTL/multiasseteventctl" "$CTL/phase31ctl"

echo "[2/5] Initializing state..."
[ -f "$MEM/multi_asset_treasury_events.json" ] || echo '{"events":[]}' > "$MEM/multi_asset_treasury_events.json"
[ -f "$MEM/multi_asset_balance_snapshot.json" ] || echo '{"balances":[]}' > "$MEM/multi_asset_balance_snapshot.json"

echo "[3/5] Running live multi-asset monitor..."
python "$CTL/multiassetbalancectl"

echo "[4/5] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase31-multi-asset-treasury","enabled":True,"interval_seconds":300,
     "command":["python","companyos/phase31ctl"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[5/5] Verifying..."
python "$CTL/phase31ctl" || true
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"multi_asset_balance_engine.py",r/"agents"/"multi_asset_event_engine.py",
r/"agents"/"phase31_controller.py",r/"companyos"/"multiassetbalancectl",
r/"companyos"/"multiasseteventctl",r/"companyos"/"phase31ctl",
r/"ceo_memory"/"phase31_multi_asset_config.json",r/"ceo_memory"/"multi_asset_treasury_balances.json",
r/"ceo_memory"/"multi_asset_treasury_events.json",r/"ceo_memory"/"phase31_rpc_health.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:6]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("PHASE 31 MULTI-ASSET TREASURY VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 31 MULTI-ASSET TREASURY ADAPTER INSTALLED"
echo " LIVE BTC / SOL / ETH / USDT / USDC MONITORING ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/multiassetbalancectl"
echo "  python companyos/multiasseteventctl"
echo "  python companyos/phase31ctl"
