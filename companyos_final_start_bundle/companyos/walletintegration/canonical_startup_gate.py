from __future__ import annotations
import json, os
from pathlib import Path

PRIMARY_WALLET = "5DRKXC4SD4TfSTPG8aQej7kBbzrtX8Tgpn4PgRbTnCnQ"

def root():
    return Path(__file__).resolve().parents[2]

def registry_wallet():
    p = root()/"ceo_memory"/"treasury_wallet_registry.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
    except Exception:
        return None
    for w in data.get("wallets", []):
        if isinstance(w, dict) and w.get("label") == "companyos-solana":
            return w.get("address")
    return None

def verify_startup():
    from companyos.walletintegration.canonical_signer import signer_status, load_canonical_signer
    registered = registry_wallet()
    if registered != PRIMARY_WALLET:
        return {"ready": False, "reason": "registry_primary_wallet_mismatch",
                "registered_wallet": registered, "expected_wallet": PRIMARY_WALLET}
    status = signer_status()
    if status.get("status") != "READY":
        return {"ready": False, "reason": status.get("reason","canonical_signer_not_ready")}
    loaded = load_canonical_signer()
    return {
        "ready": True,
        "reason": "canonical_startup_gate_ready",
        "wallet": loaded.get("wallet"),
        "registered_wallet": registered,
        "rpc_loaded": bool(os.environ.get("SOLANA_RPC_URL")),
        "private_key_loaded": bool(os.environ.get("SOLANA_PRIVATE_KEY")),
        "private_key_displayed": False,
    }

def require_startup():
    r = verify_startup()
    if not r.get("ready"):
        raise RuntimeError("COMPANYOS_STARTUP_BLOCKED:"+str(r.get("reason")))
    return r
