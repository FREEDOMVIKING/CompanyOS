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
