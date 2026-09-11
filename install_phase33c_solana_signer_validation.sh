#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
SECURE="$HOME/.companyos_secure"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase33c_solana_signer_validation_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$SECURE" "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 33C - SOLANA SIGNER VALIDATION & DRY BUILD"
echo "============================================================"

cat > "$AGENTS/solana_signer_validation.py" <<'PY'
#!/usr/bin/env python3
import json, os, subprocess, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
REG=MEM/"treasury_wallet_registry.json"
OUT=MEM/"solana_signer_validation_report.json"
HEALTH=MEM/"solana_signer_validation_health.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:
        return json.loads(p.read_text())
    except:
        return d

def rpc(url,method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as r:
        j=json.loads(r.read().decode())
    if j.get("error"):
        raise RuntimeError(j["error"])
    return j.get("result")

def main():
    rpc_url=os.getenv("SOLANA_RPC_URL","").strip()
    signer_cmd=os.getenv("SOLANA_SIGNER_COMMAND","").strip()

    wallets=[w for w in load(REG,{}).get("wallets",[]) if w.get("chain")=="solana" and w.get("enabled")]
    source=wallets[0]["address"] if wallets else None

    report={
        "generated_at":now(),
        "rpc_configured":bool(rpc_url),
        "signer_configured":bool(signer_cmd),
        "registered_source":source,
        "checks":{}
    }

    if not rpc_url or not signer_cmd or not source:
        report["success"]=False
        report["status"]="missing_configuration"
        OUT.write_text(json.dumps(report,indent=2))
        HEALTH.write_text(json.dumps({"healthy":False,"last_checked_at":now()},indent=2))
        print(json.dumps(report,indent=2))
        raise SystemExit(1)

    bal=rpc(rpc_url,"getBalance",[source,{"commitment":"confirmed"}])
    report["checks"]["live_balance_lamports"]=(bal or {}).get("value",0)

    latest=rpc(rpc_url,"getLatestBlockhash",[{"commitment":"confirmed"}])
    blockhash=(latest or {}).get("value",{}).get("blockhash")
    report["checks"]["recent_blockhash_available"]=bool(blockhash)

    payload={
        "action":"build_and_sign_sol_transfer",
        "proposal_id":"phase33c-dry-validation",
        "source":source,
        "destination":source,
        "lamports":1,
        "recent_blockhash":blockhash
    }

    p=subprocess.run(
        [signer_cmd],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        timeout=120
    )

    report["checks"]["signer_return_code"]=p.returncode
    try:
        signer_result=json.loads(p.stdout.strip() or "{}")
    except Exception:
        signer_result={"raw_stdout":p.stdout[-1000:]}

    report["checks"]["signer_result"]=signer_result
    report["checks"]["source_key_match"]=(
        signer_result.get("source")==source and signer_result.get("status")=="signed"
    )
    report["checks"]["signed_transaction_generated"]=bool(
        signer_result.get("signed_transaction_base64")
    )

    # DRY VALIDATION ONLY: no broadcast. We intentionally do not call sendTransaction.
    report["checks"]["broadcast_attempted"]=False

    report["success"]=all([
        report["checks"]["recent_blockhash_available"],
        report["checks"]["source_key_match"],
        report["checks"]["signed_transaction_generated"],
        not report["checks"]["broadcast_attempted"]
    ])
    report["status"]="solana_signer_validation_complete" if report["success"] else "solana_signer_validation_failed"

    OUT.write_text(json.dumps(report,indent=2))
    HEALTH.write_text(json.dumps({"healthy":report["success"],"last_checked_at":now()},indent=2))
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report["success"] else 1)

if __name__=="__main__":
    main()
PY
chmod +x "$AGENTS/solana_signer_validation.py"

cat > "$CTL/solanasignervalidationctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"solana_signer_validation.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/solanasignervalidationctl"

cat > "$AGENTS/phase33c_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase33c_state.json";HEALTH=MEM/"phase33c_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

p=subprocess.run([sys.executable,"companyos/solanasignervalidationctl"],cwd=ROOT,text=True,capture_output=True,timeout=180)
ok=p.returncode==0
state={
    "last_run_at":now(),
    "failure_count":0 if ok else 1,
    "stdout":p.stdout[-4000:],
    "stderr":p.stderr[-1000:]
}
save(STATE,state)
save(HEALTH,{"healthy":ok,"last_checked_at":now()})
print(json.dumps({"success":ok,"status":"phase33c_validation_complete","state":state},indent=2))
raise SystemExit(0 if ok else 1)
PY
chmod +x "$AGENTS/phase33c_controller.py"

cat > "$CTL/phase33cctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase33c_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase33cctl"

echo "[1/4] Compiling..."
python -m py_compile \
  "$AGENTS/solana_signer_validation.py" \
  "$AGENTS/phase33c_controller.py" \
  "$CTL/solanasignervalidationctl" \
  "$CTL/phase33cctl"

echo "[2/4] Running signer validation..."
source "$HOME/.companyos_secrets"
python "$CTL/solanasignervalidationctl"

echo "[3/4] Controller check..."
python "$CTL/phase33cctl"

echo "[4/4] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos"
errors=[]
req=[
    r/"agents"/"solana_signer_validation.py",
    r/"agents"/"phase33c_controller.py",
    r/"companyos"/"solanasignervalidationctl",
    r/"companyos"/"phase33cctl",
    r/"ceo_memory"/"solana_signer_validation_report.json",
    r/"ceo_memory"/"solana_signer_validation_health.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

for p in req[:4]:
    try: py_compile.compile(str(p),doraise=True)
    except Exception as e: errors.append(str(e))

rep=json.loads((r/"ceo_memory"/"solana_signer_validation_report.json").read_text())
checks=rep.get("checks",{})
if not checks.get("source_key_match"):
    errors.append("Signer source-key match failed")
if not checks.get("signed_transaction_generated"):
    errors.append("Dry signed transaction was not generated")
if checks.get("broadcast_attempted"):
    errors.append("Broadcast must remain disabled during Phase 33C validation")

print("--------------------------------------------")
print("PHASE 33C SOLANA SIGNER VALIDATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors: print("ERROR:",e)
if errors: raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 33C SOLANA SIGNER VALIDATION COMPLETE"
echo " SOURCE KEY MATCH: VERIFIED"
echo " DRY TRANSACTION BUILD: VERIFIED"
echo " BROADCAST ATTEMPTED: NO"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/solanasignervalidationctl"
echo "  python companyos/phase33cctl"
