#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
SECURE="$HOME/.companyos_secure"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$SECURE" "$MEM"
chmod 700 "$SECURE"

echo "============================================================"
echo " PHASE 33B-R2 - NODE.JS SOLANA ISOLATED LOCAL SIGNER"
echo "============================================================"

echo "[1/6] Checking Node.js..."
command -v node >/dev/null 2>&1 || pkg install -y nodejs

echo "[2/6] Ensuring secure Node dependencies..."
cd "$SECURE"

if [ ! -f package.json ]; then
cat > package.json <<'JSON'
{
  "name": "companyos-secure-signer",
  "version": "1.0.0",
  "private": true,
  "description": "Local isolated signer dependencies for CompanyOS"
}
JSON
fi

if [ ! -d node_modules/@solana/web3.js ] || [ ! -d node_modules/bs58 ]; then
  npm install @solana/web3.js bs58
fi

echo "[3/6] Installing isolated Node signer..."

cat > "$SECURE/solana_local_signer.js" <<'JS'
#!/usr/bin/env node
"use strict";

const fs = require("fs");
const web3 = require("@solana/web3.js");
const bs58pkg = require("bs58");
const bs58 = bs58pkg.default || bs58pkg;

function fail(status, message, code = 2) {
  process.stdout.write(JSON.stringify({
    success: false,
    status,
    message
  }) + "\n");
  process.exit(code);
}

function readStdin() {
  return fs.readFileSync(0, "utf8");
}

function loadKeypair() {
  const raw = (process.env.SOLANA_PRIVATE_KEY_B58 || "").trim();

  if (!raw) {
    fail(
      "missing_private_key",
      "SOLANA_PRIVATE_KEY_B58 is not configured in the secure signer environment."
    );
  }

  try {
    // Preferred format: standard base58-encoded 64-byte Solana secret key.
    const decoded = bs58.decode(raw);

    if (decoded.length === 64) {
      return web3.Keypair.fromSecretKey(Uint8Array.from(decoded));
    }

    if (decoded.length === 32) {
      return web3.Keypair.fromSeed(Uint8Array.from(decoded));
    }

    fail(
      "invalid_private_key_length",
      `Decoded private key must be 32 or 64 bytes; got ${decoded.length}.`
    );
  } catch (err) {
    fail(
      "invalid_private_key",
      `${err?.name || "Error"}: ${err?.message || String(err)}`
    );
  }
}

function main() {
  let req;

  try {
    req = JSON.parse(readStdin());
  } catch (err) {
    fail("invalid_request_json", `${err.name}: ${err.message}`);
  }

  if (req.action !== "build_and_sign_sol_transfer") {
    fail("unsupported_action", String(req.action));
  }

  const kp = loadKeypair();

  const source = String(req.source || "").trim();
  const destination = String(req.destination || "").trim();
  const recentBlockhash = String(req.recent_blockhash || "").trim();
  const lamports = Number(req.lamports);

  if (!Number.isSafeInteger(lamports) || lamports <= 0) {
    fail("invalid_lamports", "lamports must be a positive safe integer.");
  }

  const derived = kp.publicKey.toBase58();

  if (source !== derived) {
    fail(
      "source_key_mismatch",
      `Registered source does not match signer public key. expected=${source} derived=${derived}`
    );
  }

  let destinationKey;
  try {
    destinationKey = new web3.PublicKey(destination);
  } catch (err) {
    fail("invalid_destination", `${err.name}: ${err.message}`);
  }

  try {
    const tx = new web3.Transaction({
      feePayer: kp.publicKey,
      recentBlockhash
    });

    tx.add(
      web3.SystemProgram.transfer({
        fromPubkey: kp.publicKey,
        toPubkey: destinationKey,
        lamports
      })
    );

    tx.sign(kp);

    const signed = tx.serialize({
      requireAllSignatures: true,
      verifySignatures: true
    });

    process.stdout.write(JSON.stringify({
      success: true,
      status: "signed",
      source: derived,
      signed_transaction_base64: Buffer.from(signed).toString("base64")
    }) + "\n");
  } catch (err) {
    fail("signing_failed", `${err.name}: ${err.message}`);
  }
}

main();
JS

chmod 700 "$SECURE/solana_local_signer.js"

cat > "$SECURE/solana_signer_wrapper.sh" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

source "$HOME/.companyos_secrets"

exec node "$HOME/.companyos_secure/solana_local_signer.js"
SH

chmod 700 "$SECURE/solana_signer_wrapper.sh"

echo "[4/6] Node signer self-check..."
node - <<'NODE'
const w=require(process.env.HOME+"/.companyos_secure/node_modules/@solana/web3.js");
console.log("SOLANA WEB3 OK:", Boolean(w.Keypair && w.Transaction && w.SystemProgram));
NODE

echo "[5/6] Updating local signer instructions..."

cat > "$SECURE/solana_signer_setup.txt" <<'TXT'
Add these lines to ~/.companyos_secrets:

export SOLANA_PRIVATE_KEY_B58='YOUR_DEDICATED_TREASURY_PRIVATE_KEY_BASE58'
export SOLANA_SIGNER_COMMAND="$HOME/.companyos_secure/solana_signer_wrapper.sh"

Then run:

source ~/.companyos_secrets
cd ~/companyos
python companyos/solanaexecutionctl status

Expected:
  rpc_configured: true
  signer_configured: true
  automatic_signing: true
  automatic_broadcast: true

Security:
- Never commit ~/.companyos_secrets
- Never commit ~/.companyos_secure
- Never paste the private key into chat
- The signer refuses to sign if the private key does not derive the registered source address
TXT

echo "[6/6] Verifying configuration state..."

source "$HOME/.companyos_secrets" 2>/dev/null || true

python - <<'PY'
import json, os
from pathlib import Path

home = Path.home()
root = home / "companyos"
secure = home / ".companyos_secure"

status = {
    "node_signer_installed": (secure / "solana_local_signer.js").exists(),
    "wrapper_installed": (secure / "solana_signer_wrapper.sh").exists(),
    "web3_installed": (secure / "node_modules" / "@solana" / "web3.js").exists(),
    "bs58_installed": (secure / "node_modules" / "bs58").exists(),
    "solana_private_key_available": bool(os.getenv("SOLANA_PRIVATE_KEY_B58", "").strip()),
    "solana_signer_command_configured": bool(os.getenv("SOLANA_SIGNER_COMMAND", "").strip()),
    "ready_for_live_signing": bool(
        os.getenv("SOLANA_PRIVATE_KEY_B58", "").strip()
        and os.getenv("SOLANA_SIGNER_COMMAND", "").strip()
    ),
    "note": "No transaction was signed or broadcast during installation."
}

(root / "ceo_memory" / "phase33b_node_signer_status.json").write_text(
    json.dumps(status, indent=2)
)

print(json.dumps(status, indent=2))
PY

echo
echo "============================================================"
echo " PHASE 33B-R2 NODE.JS SOLANA SIGNER INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "NEXT:"
echo "  nano ~/.companyos_secrets"
echo
echo "Add:"
echo "  export SOLANA_PRIVATE_KEY_B58='YOUR_DEDICATED_TREASURY_PRIVATE_KEY_BASE58'"
echo '  export SOLANA_SIGNER_COMMAND="$HOME/.companyos_secure/solana_signer_wrapper.sh"'
echo
echo "Then:"
echo "  source ~/.companyos_secrets"
echo "  cd ~/companyos"
echo "  python companyos/solanaexecutionctl status"
echo
echo "DO NOT paste the private key into chat."
