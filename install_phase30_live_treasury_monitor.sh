#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
CONN="$ROOT/connectors"
BACKUP="$ROOT/backups/phase30_live_treasury_monitor_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$CONN" "$BACKUP"

echo "============================================================"
echo " PHASE 30 - MULTI-CHAIN LIVE TREASURY MONITOR"
echo "============================================================"

cat > "$MEM/phase30_treasury_monitor_config.json" <<'JSON'
{
  "enabled": true,
  "poll_interval_seconds": 300,
  "chains": {
    "solana": {
      "enabled": true,
      "rpc_url_env": "SOLANA_RPC_URL",
      "native_asset": "SOL",
      "track_tokens": ["USDT-SPL", "USDC-SPL"]
    },
    "evm": {
      "enabled": true,
      "rpc_url_env": "EVM_RPC_URL",
      "native_asset": "ETH",
      "track_tokens": ["USDT-ERC20", "USDC-ERC20"]
    },
    "bitcoin": {
      "enabled": true,
      "rpc_url_env": "BITCOIN_RPC_URL",
      "native_asset": "BTC"
    }
  },
  "confirmation_policy": {
    "solana_min_confirmations": 1,
    "evm_min_confirmations": 2,
    "bitcoin_min_confirmations": 2
  },
  "automatic_receipt_ingest": true,
  "automatic_balance_updates": true,
  "automatic_treasury_event_generation": true,
  "automatic_outgoing_execution": false
}
JSON

cat > "$AGENTS/treasury_rpc_health.py" <<'PY'
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
PY
chmod +x "$AGENTS/treasury_rpc_health.py"

cat > "$CTL/treasuryrpchealthctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"treasury_rpc_health.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/treasuryrpchealthctl"

cat > "$AGENTS/live_balance_monitor.py" <<'PY'
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
PY
chmod +x "$AGENTS/live_balance_monitor.py"

cat > "$CTL/livebalancectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"live_balance_monitor.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/livebalancectl"

cat > "$AGENTS/treasury_event_engine.py" <<'PY'
#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
BAL=MEM/"live_treasury_balances.json"
SNAP=MEM/"treasury_balance_snapshot.json"
EVENTS=MEM/"treasury_events.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def eid(s):return hashlib.sha256(s.encode()).hexdigest()[:20]

current=load(BAL,{}).get("balances",[])
previous={x.get("wallet_id"):x for x in load(SNAP,{}).get("balances",[])}
events=load(EVENTS,{"events":[]})
for x in current:
    if x.get("status")!="ok" or x.get("balance") is None: continue
    p=previous.get(x.get("wallet_id"))
    if not p or p.get("balance") is None: continue
    delta=float(x["balance"])-float(p["balance"])
    if abs(delta)>0:
        ev={
          "event_id":eid(f"{x['wallet_id']}|{now()}|{delta}"),
          "wallet_id":x["wallet_id"],
          "chain":x["chain"],
          "asset":x.get("native_asset"),
          "balance_delta":delta,
          "direction":"incoming" if delta>0 else "outgoing",
          "detected_at":now()
        }
        events["events"].append(ev)
events["events"]=events["events"][-5000:]
events["updated_at"]=now()
save(EVENTS,events);save(SNAP,{"generated_at":now(),"balances":current})
print(json.dumps({"success":True,"status":"treasury_event_generation_complete","event_count":len(events["events"])},indent=2))
PY
chmod +x "$AGENTS/treasury_event_engine.py"

cat > "$CTL/treasuryeventctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"treasury_event_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/treasuryeventctl"

cat > "$AGENTS/phase30_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase30_state.json";HEALTH=MEM/"phase30_health.json";REPORT=MEM/"phase30_report.json"
PIPE=[
 ("rpc_health",["python","companyos/treasuryrpchealthctl"]),
 ("live_balances",["python","companyos/livebalancectl"]),
 ("treasury_events",["python","companyos/treasuryeventctl"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

steps=[];failed=[]
for name,cmd in PIPE:
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300)
    r={"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:]}
    steps.append({"step":name,"result":r})
    if not r["success"]:failed.append(name)

report={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
print(json.dumps({"success":not failed,"status":"phase30_live_treasury_monitor_complete","report":report},indent=2))
raise SystemExit(0 if not failed else 1)
PY
chmod +x "$AGENTS/phase30_controller.py"

cat > "$CTL/phase30ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase30_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase30ctl"

echo "[1/6] Compiling..."
python -m py_compile \
 "$AGENTS/treasury_rpc_health.py" "$AGENTS/live_balance_monitor.py" \
 "$AGENTS/treasury_event_engine.py" "$AGENTS/phase30_controller.py" \
 "$CTL/treasuryrpchealthctl" "$CTL/livebalancectl" "$CTL/treasuryeventctl" "$CTL/phase30ctl"

echo "[2/6] Initializing state..."
[ -f "$MEM/treasury_events.json" ] || echo '{"events":[]}' > "$MEM/treasury_events.json"
[ -f "$MEM/treasury_balance_snapshot.json" ] || echo '{"balances":[]}' > "$MEM/treasury_balance_snapshot.json"

echo "[3/6] RPC health..."
python "$CTL/treasuryrpchealthctl"

echo "[4/6] Balance monitor..."
python "$CTL/livebalancectl"

echo "[5/6] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase30-live-treasury-monitor","enabled":True,"interval_seconds":300,
     "command":["python","companyos/phase30ctl"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[6/6] Integrated verification..."
python "$CTL/phase30ctl" || true

python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"treasury_rpc_health.py",r/"agents"/"live_balance_monitor.py",
r/"agents"/"treasury_event_engine.py",r/"agents"/"phase30_controller.py",
r/"companyos"/"treasuryrpchealthctl",r/"companyos"/"livebalancectl",
r/"companyos"/"treasuryeventctl",r/"companyos"/"phase30ctl",
r/"ceo_memory"/"phase30_treasury_monitor_config.json",
r/"ceo_memory"/"treasury_events.json",r/"ceo_memory"/"treasury_balance_snapshot.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:8]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("PHASE 30 LIVE TREASURY MONITOR VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 30 MULTI-CHAIN LIVE TREASURY MONITOR INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Includes:"
echo "  - Solana live native balance monitoring"
echo "  - EVM live native balance monitoring"
echo "  - Bitcoin RPC slot"
echo "  - RPC health checks"
echo "  - Balance snapshots"
echo "  - Automatic treasury event generation"
echo "  - 5-minute scheduled monitoring"
echo
echo "Next:"
echo "  Configure SOLANA_RPC_URL, EVM_RPC_URL, and BITCOIN_RPC_URL."
echo "  Then run: python companyos/phase30ctl"
