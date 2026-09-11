#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
SECURE="$HOME/.companyos_secure"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase33b_solana_local_signer_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$SECURE" "$MEM" "$BACKUP"
chmod 700 "$SECURE"

echo "============================================================"
echo " PHASE 33B - SOLANA ISOLATED LOCAL SIGNER"
echo "============================================================"

echo "[1/5] Checking Python signer dependency..."
python - <<'PY' || {
import solders
print("solders available")
PY
  echo "Installing solders..."
  python -m pip install --upgrade solders
}

cat > "$SECURE/solana_local_signer.py" <<'PY'
#!/usr/bin/env python3
import base64
import json
import os
import sys

from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction

def fail(status, message, code=2):
    print(json.dumps({"success": False, "status": status, "message": message}))
    raise SystemExit(code)

def load_keypair():
    secret = os.getenv("SOLANA_PRIVATE_KEY_B58", "").strip()
    if not secret:
        fail("missing_private_key", "SOLANA_PRIVATE_KEY_B58 is not configured.")
    try:
        return Keypair.from_base58_string(secret)
    except Exception as e:
        fail("invalid_private_key", f"{type(e).__name__}: {e}")

def main():
    try:
        req = json.load(sys.stdin)
    except Exception as e:
        fail("invalid_request_json", f"{type(e).__name__}: {e}")

    if req.get("action") != "build_and_sign_sol_transfer":
        fail("unsupported_action", str(req.get("action")))

    kp = load_keypair()
    source = str(req.get("source", "")).strip()
    destination = str(req.get("destination", "")).strip()
    blockhash_text = str(req.get("recent_blockhash", "")).strip()

    try:
        lamports = int(req.get("lamports"))
    except Exception:
        fail("invalid_lamports", "lamports must be an integer")

    if lamports <= 0:
        fail("invalid_lamports", "lamports must be greater than zero")

    derived = str(kp.pubkey())
    if source != derived:
        fail(
            "source_key_mismatch",
            f"Registered source address does not match signer public key. expected={source} derived={derived}",
        )

    try:
        to_pubkey = Pubkey.from_string(destination)
        recent_blockhash = Hash.from_string(blockhash_text)
    except Exception as e:
        fail("invalid_transaction_input", f"{type(e).__name__}: {e}")

    ix = transfer(
        TransferParams(
            from_pubkey=kp.pubkey(),
            to_pubkey=to_pubkey,
            lamports=lamports,
        )
    )

    try:
        message = Message.new_with_blockhash([ix], kp.pubkey(), recent_blockhash)
        tx = Transaction([kp], message, recent_blockhash)
        encoded = base64.b64encode(bytes(tx)).decode("ascii")
    except Exception as e:
        fail("signing_failed", f"{type(e).__name__}: {e}")

    print(json.dumps({
        "success": True,
        "status": "signed",
        "source": derived,
        "signed_transaction_base64": encoded
    }))

if __name__ == "__main__":
    main()
PY

chmod 700 "$SECURE/solana_local_signer.py"

cat > "$SECURE/solana_signer_wrapper.sh" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
source "$HOME/.companyos_secrets"
exec python "$HOME/.companyos_secure/solana_local_signer.py"
SH

chmod 700 "$SECURE/solana_signer_wrapper.sh"

echo "[2/5] Compiling signer..."
python -m py_compile "$SECURE/solana_local_signer.py"

echo "[3/5] Writing signer command helper..."
python - <<'PY'
from pathlib import Path
p=Path.home()/".companyos_secure"/"signer_setup_instructions.txt"
p.write_text("""Add these lines to ~/.companyos_secrets:

export SOLANA_PRIVATE_KEY_B58='YOUR_DEDICATED_TREASURY_PRIVATE_KEY_BASE58'
export SOLANA_SIGNER_COMMAND=\"$HOME/.companyos_secure/solana_signer_wrapper.sh\"

Do not commit ~/.companyos_secrets or ~/.companyos_secure to GitHub.
The signer verifies that the private key derives the registered source address before signing.
""")
print(p)
PY

echo "[4/5] Verifying no secret was embedded..."
if grep -R "SOLANA_PRIVATE_KEY_B58=.*[1-9A-HJ-NP-Za-km-z][1-9A-HJ-NP-Za-km-z]" "$ROOT" \
   --exclude-dir=.git --exclude='*.pyc' 2>/dev/null | grep -v "os.getenv" | grep -v "YOUR_DEDICATED"; then
  echo "ERROR: possible private-key material found inside repository"
  exit 1
fi

echo "[5/5] Signer readiness test..."
source "$HOME/.companyos_secrets" 2>/dev/null || true

python - <<'PY'
import json, os, subprocess
from pathlib import Path

cmd = os.getenv("SOLANA_SIGNER_COMMAND","").strip()
key = os.getenv("SOLANA_PRIVATE_KEY_B58","").strip()

result = {
    "signer_command_configured": bool(cmd),
    "private_key_available_to_secure_signer": bool(key),
    "ready_for_live_signing": bool(cmd and key),
    "note": "No live transaction was signed or broadcast during installation."
}

Path.home().joinpath("companyos","ceo_memory","phase33b_signer_status.json").write_text(
    json.dumps(result, indent=2)
)
print(json.dumps(result, indent=2))
PY

echo
echo "============================================================"
echo " PHASE 33B SOLANA ISOLATED LOCAL SIGNER INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "NEXT MANUAL SECURITY STEP:"
echo "  nano ~/.companyos_secrets"
echo
echo "Add:"
echo "  export SOLANA_PRIVATE_KEY_B58='YOUR_DEDICATED_TREASURY_PRIVATE_KEY_BASE58'"
echo '  export SOLANA_SIGNER_COMMAND="$HOME/.companyos_secure/solana_signer_wrapper.sh"'
echo
echo "Then:"
echo "  source ~/.companyos_secrets"
echo "  python companyos/solanaexecutionctl status"
echo
echo "DO NOT paste the private key into chat or commit it to GitHub."
