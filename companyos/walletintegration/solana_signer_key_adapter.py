from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from companyos.walletintegration.adaptive_solana_key import decode_solana_private_key, inspect_solana_private_key

@dataclass(frozen=True)
class SolanaSignerMaterial:
    detected_encoding: str
    key_length: int
    secret_bytes: bytes
    public_address: Optional[str]

def load_signer_material(secret: str, encoding: str = "auto") -> SolanaSignerMaterial:
    raw, detected = decode_solana_private_key(secret, encoding)
    if len(raw) not in (32, 64):
        raise ValueError(f"unsupported_solana_secret_length:{len(raw)}")
    info = inspect_solana_private_key(secret, encoding)
    return SolanaSignerMaterial(detected, len(raw), raw, info.public_key)
