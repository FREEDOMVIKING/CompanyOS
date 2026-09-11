#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

# Load CompanyOS live configuration.
if [ -f "$ROOT/.companyos_runtime/live_financial.env" ]; then
    set -a
    . "$ROOT/.companyos_runtime/live_financial.env"
    set +a
fi

# Load existing intelligence/runtime environment when present.
if [ -f "$ROOT/.companyos_runtime/live_intelligence.env" ]; then
    set -a
    . "$ROOT/.companyos_runtime/live_intelligence.env"
    set +a
fi

echo "=============================================="
echo " COMPANYOS FIRST CONTROLLED LIVE TEST"
echo "=============================================="
echo
echo "This test is limited to 0.0001 SOL."
echo "Use ONLY a Solana destination address you control."
echo

read -r -p "Destination Solana address: " DESTINATION

if [ -z "$DESTINATION" ]; then
    echo "ERROR: destination is required"
    exit 1
fi

read -r -p "Type LIVE TEST to continue: " CONFIRM

if [ "$CONFIRM" != "LIVE TEST" ]; then
    echo "Cancelled."
    exit 0
fi

export COMPANYOS_TEST_DESTINATION="$DESTINATION"

python - <<'PY'
import json
import os
import sys
import urllib.request
from pathlib import Path

from companyos.livegate import OneShotAuthorization
from companyos.controlledexec import PostExecutionLock
from companyos.liveintegration import (
    FinalLiveExecutionOrchestrator,
    LiveExecutionPolicy,
)

root = Path.home() / "companyos"
destination = os.environ["COMPANYOS_TEST_DESTINATION"]

# Extremely small first live test.
amount = 0.0001
estimated_fee = 0.00001

policy = LiveExecutionPolicy()

print("\n===== LIVE POLICY =====")
print(json.dumps(policy.snapshot(), indent=2))

if not policy.enabled:
    raise SystemExit(
        "ERROR: Live financial execution is not enabled.\n"
        "Run: bash ~/companyos/scripts/companyos_live_final.sh enable-bounded"
    )

if amount > policy.max_single:
    raise SystemExit(
        f"ERROR: test amount {amount} exceeds configured max_single "
        f"{policy.max_single}"
    )

rpc_url = os.environ.get("SOLANA_RPC_URL", "").strip()

if not rpc_url:
    raise SystemExit("ERROR: SOLANA_RPC_URL is not loaded")

# Load verified signer-derived wallet identity.
identity_paths = [
    Path.home() / "companyos_runtime" / "wallet_identity.json",
    root / ".companyos_runtime" / "wallet_identity.json",
]

identity = None

for path in identity_paths:
    if path.exists():
        try:
            candidate = json.loads(path.read_text())
            if candidate.get("public_address"):
                identity = candidate
                break
        except Exception:
            pass

if not identity:
    raise SystemExit("ERROR: verified wallet identity not found")

source = identity["public_address"]

print("\n===== SOURCE WALLET =====")
print(source)

# Query actual SOL balance.
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getBalance",
    "params": [source, {"commitment": "confirmed"}],
}

req = urllib.request.Request(
    rpc_url,
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req, timeout=30) as response:
    balance_data = json.loads(response.read().decode())

if "error" in balance_data:
    raise SystemExit(
        "ERROR: Solana balance RPC failed: "
        + json.dumps(balance_data["error"])
    )

lamports = balance_data["result"]["value"]
balance = lamports / 1_000_000_000

print("\n===== BALANCE =====")
print(f"{balance:.9f} SOL")

required = amount + estimated_fee + policy.min_reserve

if balance < required:
    raise SystemExit(
        f"ERROR: insufficient safe balance.\n"
        f"Balance: {balance:.9f} SOL\n"
        f"Required including reserve: {required:.9f} SOL"
    )

# Do not silently bypass an old post-execution lock.
lock = PostExecutionLock(root).status()

if lock.get("locked"):
    print("\n===== EXECUTION LOCK ACTIVE =====")
    print(json.dumps(lock, indent=2))
    raise SystemExit(
        "\nClear it intentionally before testing:\n"
        "bash ~/companyos/scripts/companyos_controlledexec.sh unlock"
    )

# Create single-use authorization locked to this exact destination and amount.
auth = OneShotAuthorization(root).create(
    max_amount=amount,
    destination=destination,
    ttl_seconds=300,
)

print("\n===== ONE-SHOT AUTHORIZATION =====")
print("CREATED")
print(f"Destination: {destination}")
print(f"Maximum: {amount} SOL")
print("Expires in: 5 minutes")

# Destination becomes the only permitted address for this execution.
orchestrator = FinalLiveExecutionOrchestrator(
    root,
    allowlist={destination},
)

print("\n===== EXECUTING CONTROLLED LIVE TEST =====")

result = orchestrator.execute_once(
    token=auth["token"],
    destination=destination,
    amount=amount,
    balance=balance,
    estimated_fee=estimated_fee,
    memo="CompanyOS first bounded live execution test",
)

print("\n===== FINAL RESULT =====")
print(json.dumps(result, indent=2, default=str))

status = result.get("status")

if result.get("success"):
    print("\n==============================================")
    print(" CONTROLLED LIVE EXECUTION REPORTED SUCCESS")
    print("==============================================")
    print("Verify the transaction signature/receipt above.")
    sys.exit(0)

print("\n==============================================")
print(" LIVE EXECUTION DID NOT COMPLETE")
print("==============================================")
print(f"Status: {status}")
print("No second attempt will be made automatically.")
print("The one-shot authorization has been consumed if the live gate was reached.")
print("Inspect the result above before doing anything else.")
sys.exit(1)
PY
