#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
export PYTHONPATH="$ROOT:$ROOT/companyos${PYTHONPATH:+:$PYTHONPATH}"

# Load bounded live config.
ENVFILE="$ROOT/.companyos_runtime/live_financial.env"
if [ -f "$ENVFILE" ]; then
    set -a
    . "$ENVFILE"
    set +a
fi

echo "=============================================="
echo " COMPANYOS FINAL ONE-SHOT LIVE TEST"
echo "=============================================="
echo
echo "Maximum test amount: 0.0001 SOL"
echo "No automatic retry."
echo "Execution locks again after the attempt."
echo

read -r -p "Enter a Solana address YOU control: " DEST

[ -n "$DEST" ] || {
    echo "ERROR: destination required"
    exit 1
}

read -r -p "Type exactly EXECUTE 0.0001 SOL: " CONFIRM

if [ "$CONFIRM" != "EXECUTE 0.0001 SOL" ]; then
    echo "Cancelled."
    exit 0
fi

export COMPANYOS_FINAL_DEST="$DEST"

python - <<'PY'
from pathlib import Path
import json
import os
import urllib.request
import sys

from companyos.liveintegration.live_orchestrator import (
    FinalLiveExecutionOrchestrator,
)
from companyos.livegate import OneShotAuthorization
from companyos.controlledexec import PostExecutionLock

ROOT = Path.home() / "companyos"
DEST = os.environ["COMPANYOS_FINAL_DEST"]

AMOUNT = 0.0001
ESTIMATED_FEE = 0.00001

# Explicit bounded-live controls.
os.environ["COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION"] = "true"
os.environ["COMPANYOS_AUTONOMOUS_TRANSFERS_ENABLED"] = "true"
os.environ["COMPANYOS_LIVE_MAX_SINGLE"] = "0.001"
os.environ["COMPANYOS_LIVE_MAX_DAILY"] = "0.005"
os.environ["COMPANYOS_LIVE_MIN_RESERVE"] = "0.01"
os.environ["COMPANYOS_LIVE_REQUIRE_ALLOWLIST"] = "true"

# Refuse to continue if a previous execution lock is active.
lock = PostExecutionLock(ROOT)
lock_state = lock.status()

if lock_state.get("locked"):
    print(json.dumps({
        "success": False,
        "status": "post_execution_lock_active",
        "lock": lock_state
    }, indent=2))

    raise SystemExit(
        "\nExecution is locked from a previous attempt.\n"
        "Review it before intentionally clearing the lock."
    )

# Load verified wallet identity.
identity = None

for p in [
    Path.home() / "companyos_runtime" / "wallet_identity.json",
    ROOT / ".companyos_runtime" / "wallet_identity.json",
]:
    if p.exists():
        try:
            d = json.loads(p.read_text())
            if d.get("public_address"):
                identity = d
                break
        except Exception:
            pass

if not identity:
    raise SystemExit("ERROR: verified wallet identity missing")

SOURCE = identity["public_address"]

print("\nSOURCE:", SOURCE)
print("DESTINATION:", DEST)
print("AMOUNT:", AMOUNT, "SOL")

# Get real balance from configured Solana RPC.
RPC = os.environ.get("SOLANA_RPC_URL", "").strip()

if not RPC:
    raise SystemExit("ERROR: SOLANA_RPC_URL missing")

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getBalance",
    "params": [SOURCE, {"commitment": "confirmed"}],
}

req = urllib.request.Request(
    RPC,
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req, timeout=30) as r:
    response = json.loads(r.read().decode())

if response.get("error"):
    raise SystemExit("RPC ERROR: " + json.dumps(response["error"]))

balance = response["result"]["value"] / 1_000_000_000

print("BALANCE:", balance, "SOL")

if balance - AMOUNT - ESTIMATED_FEE < 0.01:
    raise SystemExit("STOPPED: minimum reserve would not be preserved")

# Fresh authorization, exact destination, exact ceiling.
auth = OneShotAuthorization(ROOT).create(
    max_amount=AMOUNT,
    destination=DEST,
    ttl_seconds=300,
)

orch = FinalLiveExecutionOrchestrator(
    ROOT,
    allowlist={DEST},
)

print("\n===== EXECUTING ONE CONTROLLED ATTEMPT =====")

result = orch.execute_once(
    token=auth["token"],
    destination=DEST,
    amount=AMOUNT,
    balance=balance,
    estimated_fee=ESTIMATED_FEE,
    memo="CompanyOS final controlled live validation",
)

print("\n===== EXECUTION RESULT =====")
print(json.dumps(result, indent=2, default=str))

execution = result.get("execution") or {}

txid = (
    execution.get("tx_id")
    or execution.get("signature")
    or execution.get("transaction_hash")
)

print("\n===== SUMMARY =====")
print("SUCCESS:", bool(result.get("success")))
print("STATUS:", result.get("status"))
print("TX_ID:", txid or "<none returned>")
print("AUTHORIZATION_CONSUMED:", result.get("authorization_consumed"))
print("POST_EXECUTION_LOCK:", bool(result.get("post_execution_lock")))

if result.get("success") and txid:
    print("\nCONTROLLED_ONCHAIN_EXECUTION_REPORTED_SUCCESS")
    sys.exit(0)

print("\nNO VERIFIED SUCCESS YET")
print("Do not automatically retry.")
sys.exit(1)
PY
