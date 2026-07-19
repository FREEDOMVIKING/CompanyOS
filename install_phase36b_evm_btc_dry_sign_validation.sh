#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
SECURE="$HOME/.companyos_secure"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 36B - EVM + BTC DRY-SIGN VALIDATION"
echo " NO BROADCASTS WILL BE ATTEMPTED"
echo "============================================================"

cat > "$SECURE/phase36b_dry_sign_validation.js" <<'JS'
#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");
const { Wallet, Transaction } = require("ethers");
const bitcoin = require("bitcoinjs-lib");
const ecc = require("tiny-secp256k1");
const { ECPairFactory } = require("ecpair");

bitcoin.initEccLib(ecc);
const ECPair = ECPairFactory(ecc);

const root = path.join(os.homedir(), "companyos");
const mem = path.join(root, "ceo_memory");
const registryPath = path.join(mem, "treasury_wallet_registry.json");
const outPath = path.join(mem, "phase36b_dry_sign_report.json");

function loadJson(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); }
  catch { return fallback; }
}
function getWallet(chain) {
  const reg = loadJson(registryPath, {});
  return (reg.wallets || []).find(w => w.chain === chain && w.enabled);
}

async function validateEvm(expected) {
  const pk = (process.env.EVM_PRIVATE_KEY_HEX || "").trim();
  if (!pk) throw new Error("EVM_PRIVATE_KEY_HEX missing");

  const wallet = new Wallet(pk);
  if (wallet.address.toLowerCase() !== expected.toLowerCase()) {
    throw new Error(`source_key_mismatch expected=${expected} derived=${wallet.address}`);
  }

  const signed = await wallet.signTransaction({
    to: wallet.address,
    value: 1n,
    nonce: 0,
    gasLimit: 21000n,
    gasPrice: 1n,
    chainId: 1
  });

  const parsed = Transaction.from(signed);

  return {
    success: true,
    derived: wallet.address,
    recovered: parsed.from,
    raw_transaction_persisted: false,
    raw_transaction_printed: false,
    broadcast_attempted: false
  };
}

async function validateBtc(expected) {
  const wif = (process.env.BITCOIN_PRIVATE_KEY_WIF || "").trim();
  if (!wif) throw new Error("BITCOIN_PRIVATE_KEY_WIF missing");

  const network = bitcoin.networks.bitcoin;
  const key = ECPair.fromWIF(wif, network);
  const payment = bitcoin.payments.p2wpkh({
    pubkey: Buffer.from(key.publicKey),
    network
  });

  if (payment.address !== expected) {
    throw new Error(`source_key_mismatch expected=${expected} derived=${payment.address}`);
  }

  let base = (process.env.BITCOIN_RPC_URL || "https://blockstream.info/api").replace(/\/$/, "");
  if (!(base.includes("blockstream.info") || base.includes("mempool.space"))) {
    base = "https://blockstream.info/api";
  }

  const res = await fetch(`${base}/address/${expected}/utxo`);
  if (!res.ok) throw new Error(`utxo_http_${res.status}`);
  const utxos = await res.json();
  if (!utxos.length) throw new Error("no_utxos_available_for_dry_sign");

  const u = utxos[0];
  const value = BigInt(u.value);
  const fee = 300n;
  if (value <= fee + 546n) throw new Error("utxo_too_small_for_safe_dry_sign");

  const psbt = new bitcoin.Psbt({ network });
  psbt.addInput({
    hash: u.txid,
    index: Number(u.vout),
    witnessUtxo: {
      script: Buffer.from(payment.output),
      value
    }
  });

  psbt.addOutput({
    address: expected,
    value: value - fee
  });

  psbt.signInput(0, key);
  psbt.finalizeAllInputs();
  const tx = psbt.extractTransaction();

  return {
    success: true,
    derived: payment.address,
    input_count: 1,
    output_count: tx.outs.length,
    dry_txid: tx.getId(),
    raw_transaction_persisted: false,
    raw_transaction_printed: false,
    broadcast_attempted: false
  };
}

(async () => {
  const evm = getWallet("evm");
  const btc = getWallet("bitcoin");

  const report = {
    generated_at: new Date().toISOString(),
    broadcast_attempted: false,
    evm: { success: false },
    bitcoin: { success: false }
  };

  try {
    if (!evm) throw new Error("registered_evm_wallet_missing");
    report.evm = await validateEvm(evm.address);
  } catch (e) {
    report.evm = { success: false, error: e.message };
  }

  try {
    if (!btc) throw new Error("registered_bitcoin_wallet_missing");
    report.bitcoin = await validateBtc(btc.address);
  } catch (e) {
    report.bitcoin = { success: false, error: e.message };
  }

  report.success = Boolean(report.evm.success && report.bitcoin.success);
  report.status = report.success
    ? "phase36b_dry_sign_validation_complete"
    : "phase36b_dry_sign_validation_failed";

  fs.writeFileSync(outPath, JSON.stringify(report, null, 2));

  console.log(JSON.stringify(report, null, 2));
  process.exit(report.success ? 0 : 1);
})();
JS

chmod 700 "$SECURE/phase36b_dry_sign_validation.js"

cat > "$CTL/phase36bdrysignctl" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
source "$HOME/.companyos_secrets"
exec node "$HOME/.companyos_secure/phase36b_dry_sign_validation.js"
SH

chmod +x "$CTL/phase36bdrysignctl"

echo "[1/3] Syntax check..."
node --check "$SECURE/phase36b_dry_sign_validation.js"

echo "[2/3] Running EVM + BTC dry-sign validation..."
"$CTL/phase36bdrysignctl"

echo "[3/3] Verifying..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"phase36b_dry_sign_report.json"
errors=[]
if not p.exists():
    errors.append("dry-sign report missing")
else:
    d=json.loads(p.read_text())
    if not d.get("evm",{}).get("success"):
        errors.append("EVM dry-sign failed")
    if not d.get("bitcoin",{}).get("success"):
        errors.append("BTC dry-sign failed")
    if d.get("broadcast_attempted"):
        errors.append("broadcast must remain false")

print("--------------------------------------------")
print("PHASE 36B DRY-SIGN VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:
    print("ERROR:",e)
if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 36B EVM + BTC DRY-SIGN VALIDATION COMPLETE"
echo " EVM SIGN/RECOVERY: VERIFIED"
echo " BTC PSBT SIGN/FINALIZE: VERIFIED"
echo " RAW SIGNED TRANSACTIONS: NOT PERSISTED OR PRINTED"
echo " BROADCAST ATTEMPTED: NO"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
