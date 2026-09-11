from __future__ import annotations

import os
import json
from pathlib import Path

import base58
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


PRIMARY_WALLET = "5DRKXC4SD4TfSTPG8aQej7kBbzrtX8Tgpn4PgRbTnCnQ"

ROOT = Path(__file__).resolve().parents[2]

CANONICAL_ENV = (
    ROOT /
    ".companyos_runtime" /
    "live_financial.env"
)


def _read_env(path: Path) -> dict[str, str]:
    values = {}

    if not path.exists():
        return values

    for line in path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines():

        line = line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split("=", 1)

        values[key.strip()] = (
            value.strip()
            .strip("'")
            .strip('"')
        )

    return values


def _derive_address(secret: str) -> str | None:
    if not secret:
        return None

    raw = None

    try:
        raw = base58.b58decode(secret)
    except Exception:
        pass

    if raw is None:
        try:
            obj = json.loads(secret)

            if isinstance(obj, list):
                raw = bytes(obj)

        except Exception:
            pass

    if raw is None:
        return None

    if len(raw) == 64:
        seed = raw[:32]

    elif len(raw) == 32:
        seed = raw

    else:
        return None

    try:
        private = Ed25519PrivateKey.from_private_bytes(seed)

        public = private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        return base58.b58encode(public).decode()

    except Exception:
        return None


def load_canonical_signer() -> dict:
    """
    Load the canonical CompanyOS Solana signer.

    Fails closed if:
      - canonical config is missing
      - private key is missing
      - signer cannot be decoded
      - signer does not derive PRIMARY_WALLET

    Secret material is never returned in status output.
    """

    env = _read_env(CANONICAL_ENV)

    secret = env.get(
        "SOLANA_PRIVATE_KEY",
        "",
    ).strip()

    if not secret:
        raise RuntimeError(
            "CANONICAL_SIGNER_MISSING"
        )

    derived = _derive_address(secret)

    if not derived:
        raise RuntimeError(
            "CANONICAL_SIGNER_INVALID"
        )

    if derived != PRIMARY_WALLET:
        raise RuntimeError(
            "CANONICAL_SIGNER_WALLET_MISMATCH"
        )

    # Install only after successful verification.
    os.environ["SOLANA_PRIVATE_KEY"] = secret

    if env.get("SOLANA_RPC_URL"):
        os.environ["SOLANA_RPC_URL"] = env[
            "SOLANA_RPC_URL"
        ]

    return {
        "ready": True,
        "wallet": derived,
        "source": str(CANONICAL_ENV),
        "private_key_loaded": True,
        "private_key_displayed": False,
    }


def signer_status() -> dict:
    try:
        result = load_canonical_signer()

        return {
            "status": "READY",
            "wallet": result["wallet"],
            "source": result["source"],
            "private_key": "HIDDEN",
        }

    except Exception as exc:
        return {
            "status": "BLOCKED",
            "reason": str(exc),
            "wallet": PRIMARY_WALLET,
            "private_key": "HIDDEN",
        }
