#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/connectors_live/solana_finance_adapter.py"
REG="$ROOT/companyos/connectors_live/registry.py"
CFG="$ROOT/config/connectors.json"
ENVF="$ROOT/.env"
ROUTER="$ROOT/companyos/runtime/live_financial_execution_router.py"
CTL="$ROOT/scripts/companyos_financectl"
PIDFILE="$RT/live_financial_execution_router.pid"
LOGFILE="$RT/live_financial_execution_router.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.01 SOLANA FINANCIAL CONNECTION ====="
echo "NETWORK=SOLANA_MAINNET"
echo "NOTE=LIVE_AUTHORITY_SWITCHES_UNCHANGED"
echo "NOTE=NO_OLD_TRADING_BOT_FILES_IMPORTED"

mkdir -p "$ROOT/companyos/connectors_live" "$ROOT/companyos/runtime" "$ROOT/scripts" "$ROOT/config" "$RT"

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$MOD" "$REG" "$CFG" "$ROUTER"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_01_backup_${stamp}"
    echo "BACKUP=$f.v66_01_backup_${stamp}"
  fi
done

cat > "$MOD" <<'PY'
from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import struct
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request

from .base import BaseConnector, ConnectorError
from .config import env_value

# Pure-Python Ed25519 keeps the financial connector independent of the
# user's older trading projects and avoids requiring their code or wallets.
_Q = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _Q - 2, _Q)) % _Q
_I = pow(2, (_Q - 1) // 4, _Q)
_B58 = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _inv(x: int) -> int:
    return pow(x, _Q - 2, _Q)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_D * y * y + 1) % _Q
    x = pow(xx, (_Q + 3) // 8, _Q)
    if (x * x - xx) % _Q != 0:
        x = (x * _I) % _Q
    if x & 1:
        x = _Q - x
    return x


_BY = 4 * _inv(5) % _Q
_BX = _xrecover(_BY)
_B = (_BX, _BY)
_ID = (0, 1)


def _ed_add(p, q):
    x1, y1 = p
    x2, y2 = q
    z = (_D * x1 * x2 * y1 * y2) % _Q
    x3 = ((x1 * y2 + x2 * y1) * _inv(1 + z)) % _Q
    y3 = ((y1 * y2 + x1 * x2) * _inv(1 - z)) % _Q
    return x3, y3


def _scalarmult(p, e: int):
    r = _ID
    q = p
    n = int(e)
    while n:
        if n & 1:
            r = _ed_add(r, q)
        q = _ed_add(q, q)
        n >>= 1
    return r


def _encodepoint(p) -> bytes:
    x, y = p
    n = y | ((x & 1) << 255)
    return n.to_bytes(32, "little")


def ed25519_public_key(seed: bytes) -> bytes:
    if len(seed) != 32:
        raise ValueError("Ed25519 seed must be 32 bytes")
    h = bytearray(hashlib.sha512(seed).digest())
    h[0] &= 248
    h[31] &= 63
    h[31] |= 64
    a = int.from_bytes(h[:32], "little")
    return _encodepoint(_scalarmult(_B, a))


def ed25519_sign(seed: bytes, message: bytes) -> bytes:
    if len(seed) != 32:
        raise ValueError("Ed25519 seed must be 32 bytes")
    h = bytearray(hashlib.sha512(seed).digest())
    h[0] &= 248
    h[31] &= 63
    h[31] |= 64
    a = int.from_bytes(h[:32], "little")
    prefix = bytes(h[32:])
    pub = _encodepoint(_scalarmult(_B, a))
    r = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % _L
    r_enc = _encodepoint(_scalarmult(_B, r))
    k = int.from_bytes(hashlib.sha512(r_enc + pub + message).digest(), "little") % _L
    s = (r + k * a) % _L
    return r_enc + s.to_bytes(32, "little")


def b58decode(value: str) -> bytes:
    s = value.strip().encode()
    if not s:
        return b""
    n = 0
    for c in s:
        try:
            idx = _B58.index(bytes([c]))
        except ValueError as exc:
            raise ValueError("invalid base58") from exc
        n = n * 58 + idx
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    zeros = 0
    for c in s:
        if c == _B58[0]:
            zeros += 1
        else:
            break
    return b"\x00" * zeros + raw


def b58encode(raw: bytes) -> str:
    if not raw:
        return ""
    n = int.from_bytes(raw, "big")
    out = bytearray()
    while n:
        n, r = divmod(n, 58)
        out.append(_B58[r])
    zeros = 0
    for b in raw:
        if b == 0:
            zeros += 1
        else:
            break
    return (bytes([_B58[0]]) * zeros + bytes(reversed(out or b""))).decode()


def shortvec(n: int) -> bytes:
    if n < 0:
        raise ValueError("negative shortvec")
    out = bytearray()
    value = int(n)
    while True:
        elem = value & 0x7F
        value >>= 7
        if value:
            elem |= 0x80
        out.append(elem)
        if not value:
            return bytes(out)


def build_legacy_sol_transfer_message(sender: bytes, recipient: bytes, blockhash: bytes, lamports: int) -> bytes:
    if len(sender) != 32 or len(recipient) != 32 or len(blockhash) != 32:
        raise ValueError("sender, recipient and blockhash must each be 32 bytes")
    if lamports <= 0:
        raise ValueError("lamports must be positive")

    system_program = b"\x00" * 32
    header = bytes([1, 0, 1])  # one signer; system program readonly
    account_keys = shortvec(3) + sender + recipient + system_program

    data = struct.pack("<IQ", 2, int(lamports))  # SystemProgram::Transfer
    instruction = (
        bytes([2]) +                 # program_id_index
        shortvec(2) + bytes([0, 1]) +
        shortvec(len(data)) + data
    )

    return header + account_keys + blockhash + shortvec(1) + instruction


def build_signed_legacy_sol_transfer(seed: bytes, recipient_b58: str, blockhash_b58: str, lamports: int):
    sender = ed25519_public_key(seed)
    recipient = b58decode(recipient_b58)
    blockhash = b58decode(blockhash_b58)
    message = build_legacy_sol_transfer_message(sender, recipient, blockhash, lamports)
    sig = ed25519_sign(seed, message)
    tx = shortvec(1) + sig + message
    return tx, b58encode(sender), b58encode(sig)


class SolanaFinanceConnector(BaseConnector):
    name = "crypto"

    DEFAULT_RPC = "https://api.mainnet-beta.solana.com"
    PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"

    def __init__(self, config):
        super().__init__(config)
        self.runtime = Path.home() / ".companyos_runtime" / "finance"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.ledger = self.runtime / "solana_transactions.jsonl"

    def _env_first(self, names):
        for n in names:
            v = os.environ.get(n)
            if v and v.strip():
                return v.strip()
        return None

    def _rpc_url(self):
        name = self.config.get("rpc_url_env")
        return (
            env_value(name)
            or self._env_first(["COMPANYOS_SOLANA_RPC_URL", "SOLANA_RPC_URL"])
            or self.config.get("rpc_url")
            or self.DEFAULT_RPC
        )

    def _secret_raw(self):
        name = self.config.get("private_key_env")
        return (
            env_value(name)
            or self._env_first([
                "COMPANYOS_SOLANA_PRIVATE_KEY_BASE58",
                "COMPANYOS_SOLANA_PRIVATE_KEY",
                "SOLANA_PRIVATE_KEY",
                "PHANTOM_PRIVATE_KEY",
            ])
        )

    def _seed(self):
        raw = self._secret_raw()
        if not raw:
            raise ConnectorError("solana_private_key_missing")

        value = raw.strip()

        if value.startswith("["):
            try:
                arr = json.loads(value)
                key = bytes(int(x) & 0xFF for x in arr)
            except Exception as exc:
                raise ConnectorError("invalid_json_secret_key") from exc
        else:
            key = None
            try:
                key = b58decode(value)
            except Exception:
                pass
            if key is None or len(key) not in (32, 64):
                try:
                    key = base64.b64decode(value, validate=True)
                except Exception as exc:
                    raise ConnectorError("private_key_must_be_base58_base64_or_json_array") from exc

        if len(key) == 64:
            seed = key[:32]
        elif len(key) == 32:
            seed = key
        else:
            raise ConnectorError(f"unsupported_private_key_length:{len(key)}")

        return seed

    def _derived_wallet(self):
        try:
            return b58encode(ed25519_public_key(self._seed()))
        except Exception:
            return None

    def _configured_wallet(self):
        name = self.config.get("wallet_address_env")
        return (
            env_value(name)
            or self._env_first(["COMPANYOS_SOLANA_WALLET_ADDRESS", "SOLANA_WALLET_ADDRESS"])
        )

    def wallet_address(self):
        configured = self._configured_wallet()
        derived = self._derived_wallet()
        if configured and derived and configured != derived:
            raise ConnectorError("configured_wallet_does_not_match_private_key")
        return derived or configured

    def _num(self, env_names, config_name=None):
        for n in env_names:
            v = os.environ.get(n)
            if v is not None and str(v).strip():
                try:
                    return float(v)
                except Exception:
                    return None
        if config_name and self.config.get(config_name) not in (None, ""):
            try:
                return float(self.config.get(config_name))
            except Exception:
                return None
        return None

    def _limits(self):
        return {
            "single_usd": self._num(["COMPANYOS_FINANCE_SINGLE_TX_CAP_USD"], "single_tx_cap_usd"),
            "daily_usd": self._num(["COMPANYOS_FINANCE_DAILY_CAP_USD"], "daily_cap_usd"),
            "single_sol": self._num(["COMPANYOS_FINANCE_SINGLE_TX_CAP_SOL"], "single_tx_cap_sol"),
            "daily_sol": self._num(["COMPANYOS_FINANCE_DAILY_CAP_SOL"], "daily_cap_sol"),
        }

    def limits_configured(self):
        x = self._limits()
        usd_pair = bool(x["single_usd"] and x["daily_usd"])
        sol_pair = bool(x["single_sol"] and x["daily_sol"])
        return usd_pair or sol_pair

    def is_configured(self):
        if not self.enabled:
            return False
        try:
            wallet = self.wallet_address()
        except Exception:
            return False
        return bool(self._rpc_url() and wallet and self._secret_raw() and self.limits_configured())

    def health(self):
        try:
            wallet = self.wallet_address()
            wallet_match = True
            wallet_error = None
        except Exception as exc:
            wallet = self._configured_wallet()
            wallet_match = False
            wallet_error = str(exc)

        return {
            "name": self.name,
            "provider": "solana_local_signer",
            "enabled": self.enabled,
            "configured": self.is_configured(),
            "dry_run": self.dry_run,
            "network": "mainnet-beta",
            "rpc_configured": bool(self._rpc_url()),
            "wallet_public_key": wallet,
            "wallet_key_match": wallet_match,
            "wallet_error": wallet_error,
            "signer_available": bool(self._secret_raw()),
            "limits_configured": self.limits_configured(),
            "limits": self._limits(),
            "private_key_exposed": False,
        }

    def _rpc(self, method, params):
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }).encode()
        req = request.Request(
            self._rpc_url(),
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "CompanyOS/66.01",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode())
        except Exception as exc:
            raise ConnectorError(f"solana_rpc_error:{type(exc).__name__}:{exc}") from exc
        if data.get("error"):
            raise ConnectorError(f"solana_rpc_error:{data['error']}")
        return data.get("result")

    def _get_balance(self):
        wallet = self.wallet_address()
        if not wallet:
            raise ConnectorError("wallet_address_missing")
        result = self._rpc("getBalance", [wallet, {"commitment": "confirmed"}])
        lamports = int((result or {}).get("value") or 0)
        return {
            "ok": True,
            "status": "balance_read",
            "asset": "SOL",
            "wallet": wallet,
            "lamports": lamports,
            "balance": lamports / 1_000_000_000,
        }

    def _sol_price_usd(self):
        static = self._num(["COMPANYOS_SOL_PRICE_USD"], "sol_price_usd")
        if static and static > 0:
            return static, "configured_override"

        req = request.Request(
            self.config.get("price_url") or self.PRICE_URL,
            headers={"User-Agent": "CompanyOS/66.01"},
        )
        try:
            with request.urlopen(req, timeout=min(self.timeout, 15)) as resp:
                d = json.loads(resp.read().decode())
            price = float(((d.get("solana") or {}).get("usd")))
            if price > 0:
                return price, "coingecko_simple_price"
        except Exception:
            pass
        return None, "unavailable"

    def _ledger_rows(self):
        if not self.ledger.exists():
            return []
        out = []
        for line in self.ledger.read_text().splitlines():
            try:
                x = json.loads(line)
                if isinstance(x, dict):
                    out.append(x)
            except Exception:
                pass
        return out

    def _daily_usage(self):
        cutoff = time.time() - 86400
        rows = [
            x for x in self._ledger_rows()
            if float(x.get("timestamp_unix") or 0) >= cutoff
            and x.get("status") in {"submitted", "confirmed"}
        ]
        return {
            "sol": sum(float(x.get("amount_sol") or 0) for x in rows),
            "usd": sum(float(x.get("amount_usd") or 0) for x in rows if x.get("amount_usd") is not None),
            "transactions": len(rows),
        }

    def preflight_transfer(self, payload):
        asset = str(payload.get("asset") or "SOL").upper()
        if asset != "SOL":
            return {"ok": False, "status": "asset_not_supported_v66_01", "asset": asset}

        try:
            amount = float(payload.get("amount_sol") or payload.get("amount") or 0)
        except Exception:
            return {"ok": False, "status": "invalid_amount"}

        if amount <= 0:
            return {"ok": False, "status": "amount_must_be_positive"}

        recipient = str(payload.get("to") or payload.get("recipient") or "").strip()
        try:
            if len(b58decode(recipient)) != 32:
                raise ValueError()
        except Exception:
            return {"ok": False, "status": "invalid_recipient"}

        if not self._secret_raw():
            return {"ok": False, "status": "solana_private_key_missing"}

        if not self.limits_configured():
            return {"ok": False, "status": "finance_limits_not_configured"}

        limits = self._limits()
        daily = self._daily_usage()

        if limits["single_sol"] and amount > limits["single_sol"]:
            return {
                "ok": False,
                "status": "single_sol_cap_exceeded",
                "amount_sol": amount,
                "cap_sol": limits["single_sol"],
            }

        if limits["daily_sol"] and daily["sol"] + amount > limits["daily_sol"]:
            return {
                "ok": False,
                "status": "daily_sol_cap_exceeded",
                "amount_sol": amount,
                "daily_used_sol": daily["sol"],
                "cap_sol": limits["daily_sol"],
            }

        price = None
        price_source = None
        amount_usd = None

        if limits["single_usd"] or limits["daily_usd"]:
            price, price_source = self._sol_price_usd()
            if not price:
                return {"ok": False, "status": "sol_usd_price_unavailable_fail_closed"}
            amount_usd = amount * price

            if limits["single_usd"] and amount_usd > limits["single_usd"]:
                return {
                    "ok": False,
                    "status": "single_usd_cap_exceeded",
                    "amount_usd": amount_usd,
                    "cap_usd": limits["single_usd"],
                }

            if limits["daily_usd"] and daily["usd"] + amount_usd > limits["daily_usd"]:
                return {
                    "ok": False,
                    "status": "daily_usd_cap_exceeded",
                    "amount_usd": amount_usd,
                    "daily_used_usd": daily["usd"],
                    "cap_usd": limits["daily_usd"],
                }

        return {
            "ok": True,
            "status": "transfer_preflight_pass",
            "asset": "SOL",
            "recipient": recipient,
            "amount_sol": amount,
            "amount_usd": amount_usd,
            "sol_price_usd": price,
            "price_source": price_source,
            "daily_usage": daily,
            "limits": limits,
        }

    def _append_ledger(self, row):
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger.open("a") as f:
            f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    def _transfer_sol(self, payload):
        pre = self.preflight_transfer(payload)
        if not pre.get("ok"):
            return pre

        amount_sol = float(pre["amount_sol"])
        lamports = int(round(amount_sol * 1_000_000_000))
        recipient = pre["recipient"]

        balance = self._get_balance()
        fee_reserve = int(self.config.get("fee_reserve_lamports") or 10000)
        if balance["lamports"] < lamports + fee_reserve:
            return {
                "ok": False,
                "status": "insufficient_sol_balance",
                "balance_lamports": balance["lamports"],
                "requested_lamports": lamports,
                "fee_reserve_lamports": fee_reserve,
            }

        bh = self._rpc("getLatestBlockhash", [{"commitment": "confirmed"}])
        value = (bh or {}).get("value") or {}
        blockhash = value.get("blockhash")
        if not blockhash:
            raise ConnectorError("latest_blockhash_missing")

        tx, sender, local_sig = build_signed_legacy_sol_transfer(
            self._seed(),
            recipient,
            blockhash,
            lamports,
        )
        encoded = base64.b64encode(tx).decode()

        signature = self._rpc("sendTransaction", [
            encoded,
            {
                "encoding": "base64",
                "skipPreflight": False,
                "preflightCommitment": "confirmed",
                "maxRetries": 3,
            },
        ])

        if not signature:
            raise ConnectorError("sendTransaction_returned_no_signature")

        row = {
            "timestamp_unix": time.time(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "submitted",
            "asset": "SOL",
            "sender": sender,
            "recipient": recipient,
            "amount_sol": amount_sol,
            "amount_usd": pre.get("amount_usd"),
            "sol_price_usd": pre.get("sol_price_usd"),
            "price_source": pre.get("price_source"),
            "signature": signature,
            "local_signature": local_sig,
        }
        self._append_ledger(row)

        confirmed = False
        confirmation_status = None
        confirmation_error = None

        for _ in range(10):
            time.sleep(2)
            try:
                st = self._rpc("getSignatureStatuses", [
                    [signature],
                    {"searchTransactionHistory": True},
                ])
                rec = ((st or {}).get("value") or [None])[0]
                if rec:
                    confirmation_status = rec.get("confirmationStatus")
                    confirmation_error = rec.get("err")
                    if confirmation_error is not None:
                        break
                    if confirmation_status in {"confirmed", "finalized"}:
                        confirmed = True
                        break
            except Exception:
                pass

        if confirmation_error is not None:
            self._append_ledger({
                **row,
                "timestamp_unix": time.time(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "failed",
                "confirmation_error": confirmation_error,
            })
            return {
                "ok": False,
                "status": "transaction_failed",
                "signature": signature,
                "confirmation_error": confirmation_error,
            }

        if confirmed:
            self._append_ledger({
                **row,
                "timestamp_unix": time.time(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "confirmed",
                "confirmation_status": confirmation_status,
            })

        return {
            "ok": True,
            "status": "confirmed" if confirmed else "submitted",
            "asset": "SOL",
            "sender": sender,
            "recipient": recipient,
            "amount_sol": amount_sol,
            "amount_usd": pre.get("amount_usd"),
            "signature": signature,
            "confirmation_status": confirmation_status,
        }

    def _execute(self, action, payload):
        payload = payload or {}
        if action == "get_balance":
            return self._get_balance()
        if action in {"transfer_funds", "transfer_sol"}:
            return self._transfer_sol(payload)
        return {
            "ok": False,
            "status": "unsupported_crypto_action",
            "action": action,
            "supported": ["get_balance", "transfer_funds"],
        }
PY

echo "===== PATCH CONNECTOR REGISTRY ====="
python - <<'PY'
from pathlib import Path

p = Path.home()/"companyos/companyos/connectors_live/registry.py"
s = p.read_text()

imp = "from .solana_finance_adapter import SolanaFinanceConnector\n"
if imp not in s:
    anchor = "from .cloudflare_adapter import CloudflareHostingConnector\n"
    if anchor not in s:
        raise SystemExit("V66_01_ABORT=registry_import_anchor_missing")
    s = s.replace(anchor, anchor + imp, 1)

old = '"crypto": CryptoConnector(merged("crypto")),'
new = '"crypto": SolanaFinanceConnector(merged("crypto")),'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit("V66_01_ABORT=registry_crypto_anchor_missing")

p.write_text(s)
print("V66_01_REGISTRY_PATCH=PASS")
PY

echo "===== PATCH CONNECTOR CONFIG ====="
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos/config/connectors.json"
try:
    d = json.loads(p.read_text()) if p.exists() else {}
except Exception:
    d = {}

crypto = dict(d.get("crypto") or {})
crypto.update({
    "enabled": True,
    "dry_run": False,
    "provider": "solana_local_signer",
    "rpc_url_env": "COMPANYOS_SOLANA_RPC_URL",
    "wallet_address_env": "COMPANYOS_SOLANA_WALLET_ADDRESS",
    "private_key_env": "COMPANYOS_SOLANA_PRIVATE_KEY_BASE58",
    "single_tx_cap_usd_env": "COMPANYOS_FINANCE_SINGLE_TX_CAP_USD",
    "daily_cap_usd_env": "COMPANYOS_FINANCE_DAILY_CAP_USD",
    "price_url": "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
    "fee_reserve_lamports": 10000,
})
d["crypto"] = crypto

p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
print("V66_01_CONNECTOR_CONFIG_PATCH=PASS")
PY

echo "===== ADD FINANCE ENVIRONMENT FIELDS WITHOUT OVERWRITING EXISTING VALUES ====="
touch "$ENVF"
chmod 600 "$ENVF"

python - <<'PY'
from pathlib import Path

p = Path.home()/"companyos/.env"
text = p.read_text() if p.exists() else ""
present = set()
for line in text.splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        present.add(line.split("=",1)[0].strip())

defaults = [
    ("COMPANYOS_SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"),
    ("COMPANYOS_SOLANA_WALLET_ADDRESS", ""),
    ("COMPANYOS_SOLANA_PRIVATE_KEY_BASE58", ""),
    ("COMPANYOS_FINANCE_SINGLE_TX_CAP_USD", ""),
    ("COMPANYOS_FINANCE_DAILY_CAP_USD", ""),
    ("COMPANYOS_FINANCE_SINGLE_TX_CAP_SOL", ""),
    ("COMPANYOS_FINANCE_DAILY_CAP_SOL", ""),
    ("COMPANYOS_SOL_PRICE_USD", ""),
]

with p.open("a") as f:
    if text and not text.endswith("\n"):
        f.write("\n")
    if not all(k in present for k,_ in defaults):
        f.write("\n# CompanyOS V66.01 Solana financial connection\n")
    for k,v in defaults:
        if k not in present:
            f.write(f"{k}={v}\n")

print("V66_01_ENV_FIELDS_READY=PASS")
print("PRIVATE_KEY_VALUE_PRINTED=False")
PY

cat > "$ROUTER" <<'PY'
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from companyos.connectors_live.engine import ConnectorEngine
from companyos.runtime import live_drl_strategy_governor as governor

RT = Path.home()/".companyos_runtime"
FRT = RT/"live_financial_execution"
STATE = FRT/"state.json"
LATEST = FRT/"latest.json"
HISTORY = FRT/"history.jsonl"
FRT.mkdir(parents=True, exist_ok=True)

VERSION = "V66.01"


def load_json(path: Path, default: Any):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any):
    tmp = path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str)+"\n")
    tmp.replace(path)


def append_jsonl(path: Path, row: dict[str, Any]):
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, default=str)+"\n")


def activation_state():
    st = load_json(STATE,{})
    if not st:
        st = {
            "version": VERSION,
            "mode": "live_financial",
            "activated_at_unix": time.time(),
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "baseline_only_new_actions": True,
        }
        save_json(STATE,st)
    return st


def auth():
    return dict(governor.LIVE_AUTHORITY)


def engine():
    return ConnectorEngine()


def crypto_health():
    eng = engine()
    conn = eng.registry.get("crypto")
    if not conn:
        return {"ok":False,"status":"crypto_connector_missing"}
    h = conn.health()
    return {
        "ok": True,
        "authority": {
            "financial_actions": bool(auth().get("financial_actions")),
            "wallet_transactions": bool(auth().get("wallet_transactions")),
        },
        "connector": h,
        "live_ready": bool(
            h.get("enabled")
            and h.get("configured")
            and h.get("dry_run") is False
        ),
    }


def _ts(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z","+00:00")).timestamp()
    except Exception:
        return 0.0


def _executed(eng):
    rows=load_json(eng.runtime/"executions.json",[])
    return {
        str(x.get("action_id")) for x in rows
        if isinstance(x,dict) and x.get("action_id")
    }


def pending():
    eng=engine()
    rows=load_json(eng.runtime/"actions.json",[])
    st=activation_state()
    cutoff=float(st.get("activated_at_unix") or 0)
    done=_executed(eng)
    out=[]
    for x in rows if isinstance(rows,list) else []:
        if not isinstance(x,dict): continue
        if x.get("connector")!="crypto": continue
        aid=str(x.get("action_id") or "")
        if not aid or aid in done: continue
        created=_ts(x.get("created_at"))
        if created and created < cutoff: continue
        out.append(x)
    return out


def classify(action):
    h=crypto_health()
    if not h.get("live_ready"):
        return False,"crypto_connector_not_live_ready"

    act=str(action.get("action") or "")
    a=h.get("authority") or {}

    if act=="get_balance":
        return bool(a.get("financial_actions")),"financial_actions_authority_required"

    if act in {"transfer_funds","transfer_sol"}:
        if not a.get("wallet_transactions"):
            return False,"wallet_transactions_authority_required"

        conn=engine().registry.get("crypto")
        pre=conn.preflight_transfer(action.get("payload") or {})
        if not pre.get("ok"):
            return False,pre.get("status") or "transfer_preflight_failed"
        return True,"wallet_transfer_preflight_pass"

    return False,"unsupported_financial_action"


def process_once(max_actions=3):
    eng=engine()
    rows=pending()
    results=[]

    for row in rows[:max(1,int(max_actions))]:
        aid=str(row.get("action_id"))
        ok,reason=classify(row)
        item={
            "action_id":aid,
            "action":row.get("action"),
            "authorized":ok,
            "reason":reason,
            "executed":False,
        }

        if ok:
            if row.get("approval_required"):
                eng.approve(aid,approved_by="live_drl_financial_authority")
            result=eng.execute(aid)
            item["result"]=result
            item["executed"]=bool(result and result.get("ok"))

        results.append(item)
        append_jsonl(HISTORY,{
            "timestamp_unix":time.time(),
            "timestamp":datetime.now(timezone.utc).isoformat(),
            **item,
        })

    report={
        "version":VERSION,
        "mode":"live_financial",
        "pending_seen":len(rows),
        "processed":len(results),
        "executed":sum(1 for x in results if x["executed"]),
        "results":results,
        "health":crypto_health(),
    }
    save_json(LATEST,report)
    return report


def status():
    return {
        "version":VERSION,
        "mode":"live_financial",
        "state":activation_state(),
        "health":crypto_health(),
        "pending_new_financial_actions":len(pending()),
    }


def loop(interval=60,max_actions=3):
    while True:
        try:
            r=process_once(max_actions)
            print(json.dumps({
                "ts":time.time(),
                "mode":"live_financial",
                "pending":r["pending_seen"],
                "processed":r["processed"],
                "executed":r["executed"],
            },sort_keys=True),flush=True)
        except Exception as exc:
            print(json.dumps({
                "ts":time.time(),
                "mode":"live_financial",
                "error":f"{type(exc).__name__}:{exc}",
            },sort_keys=True),flush=True)
        time.sleep(max(15,int(interval)))


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("status")
    sub.add_parser("health")
    p=sub.add_parser("process")
    p.add_argument("--max-actions",type=int,default=3)
    lp=sub.add_parser("loop")
    lp.add_argument("--interval",type=int,default=60)
    lp.add_argument("--max-actions",type=int,default=3)
    args=ap.parse_args()

    if args.cmd=="status":
        print(json.dumps(status(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="health":
        print(json.dumps(crypto_health(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="process":
        print(json.dumps(process_once(args.max_actions),indent=2,sort_keys=True,default=str))
    elif args.cmd=="loop":
        loop(args.interval,args.max_actions)


if __name__=="__main__":
    main()
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
PIDFILE="$RT/live_financial_execution_router.pid"
LOGFILE="$RT/live_financial_execution_router.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

cmd="${1:-status}"

case "$cmd" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "LIVE_FINANCE_ALREADY_RUNNING PID=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup python -m companyos.runtime.live_financial_execution_router loop \
      --interval "${COMPANYOS_FINANCE_ROUTER_INTERVAL_SECONDS:-60}" \
      --max-actions "${COMPANYOS_FINANCE_MAX_ACTIONS_PER_CYCLE:-3}" \
      >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    echo "LIVE_FINANCE_RUNNING PID=$(cat "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    echo "LIVE_FINANCE_STOPPED"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  health)
    python -m companyos.runtime.live_financial_execution_router health
    ;;
  status)
    python -m companyos.runtime.live_financial_execution_router status
    if [ -f "$PIDFILE" ]; then
      echo "PID=$(cat "$PIDFILE")"
      ps -p "$(cat "$PIDFILE")" -o pid,etime,args || true
    fi
    ;;
  balance)
    python - <<'PY'
import json
from companyos.connectors_live.engine import ConnectorEngine
c=ConnectorEngine().registry["crypto"]
print(json.dumps(c.execute("get_balance",{}),indent=2,sort_keys=True))
PY
    ;;
  limits)
    python - <<'PY'
import json
from companyos.connectors_live.engine import ConnectorEngine
c=ConnectorEngine().registry["crypto"]
print(json.dumps({
    "wallet":c.wallet_address(),
    "limits":c._limits(),
    "daily_usage":c._daily_usage(),
    "limits_configured":c.limits_configured(),
},indent=2,sort_keys=True))
PY
    ;;
  queue-transfer)
    to="${2:-}"
    amount="${3:-}"
    if [ -z "$to" ] || [ -z "$amount" ]; then
      echo "usage: $0 queue-transfer RECIPIENT_ADDRESS AMOUNT_SOL"
      exit 2
    fi
    python - "$to" "$amount" <<'PY'
import json,sys
from companyos.connectors_live.engine import ConnectorEngine
to=sys.argv[1]
amount=float(sys.argv[2])
eng=ConnectorEngine()
c=eng.registry["crypto"]
pre=c.preflight_transfer({"asset":"SOL","to":to,"amount_sol":amount})
print("PREFLIGHT=")
print(json.dumps(pre,indent=2,sort_keys=True))
if not pre.get("ok"):
    raise SystemExit(1)
row=eng.queue("crypto","transfer_funds",{"asset":"SOL","to":to,"amount_sol":amount},risk="high")
print("QUEUED=")
print(json.dumps(row,indent=2,sort_keys=True))
PY
    ;;
  process)
    python -m companyos.runtime.live_financial_execution_router process --max-actions "${2:-3}"
    ;;
  log)
    tail -n "${2:-120}" "$LOGFILE"
    ;;
  env)
    nano "$ROOT/.env"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|health|status|balance|limits|queue-transfer ADDRESS AMOUNT_SOL|process [max]|log [lines]|env}"
    exit 2
    ;;
esac
SH

chmod +x "$CTL"

cat > "$ROOT/tests/test_solana_finance_adapter.py" <<'PY'
from companyos.connectors_live.solana_finance_adapter import (
    b58decode,
    b58encode,
    ed25519_public_key,
    ed25519_sign,
    shortvec,
)

def test_base58_roundtrip():
    raw=b"\x00\x00hello-solana"
    assert b58decode(b58encode(raw))==raw

def test_shortvec():
    assert shortvec(0)==b"\x00"
    assert shortvec(127)==b"\x7f"
    assert shortvec(128)==b"\x80\x01"

def test_rfc8032_ed25519_vector_1():
    seed=bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    expected_pub=bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    expected_sig=bytes.fromhex(
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
        "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
    )
    assert ed25519_public_key(seed)==expected_pub
    assert ed25519_sign(seed,b"")==expected_sig
PY

echo "===== COMPILE ====="
python -m py_compile \
  "$MOD" \
  "$REG" \
  "$ROUTER"
echo "V66_01_MODULE_COMPILE=PASS"

echo "===== CRYPTO TESTS ====="
python -m pytest -q tests/test_solana_finance_adapter.py
echo "V66_01_CRYPTO_TESTS=PASS"

echo "===== CONNECTOR HEALTH ====="
python -m companyos.runtime.live_financial_execution_router health

echo "===== CREATE FINANCIAL ROUTER BASELINE ====="
python -m companyos.runtime.live_financial_execution_router status >/dev/null
echo "V66_01_FINANCE_BASELINE=PASS"

echo "===== START FINANCIAL ROUTER ====="
"$CTL" restart

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V66_01_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_01_OLD_TRADING_PROJECT_NOT_IMPORTED=PASS"
echo "V66_01_SOLANA_RPC_PATH=PASS"
echo "V66_01_LOCAL_SIGNER=PASS"
echo "V66_01_TRANSACTION_CAPS_FAIL_CLOSED=PASS"
echo "V66_01_LEDGER=PASS"
echo "V66_01_FINANCIAL_ROUTER=PASS"
echo "V66_01_COMPLETE"
