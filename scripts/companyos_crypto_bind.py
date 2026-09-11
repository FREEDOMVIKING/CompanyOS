#!/usr/bin/env python3
import json, os
from pathlib import Path
from companyos.cryptoops import WalletDiscovery, ExistingWalletAdapter, CryptoPaymentConnector

root = Path.home() / "companyos"
forced = os.getenv("COMPANYOS_EXISTING_WALLET_FILE","").strip()

if forced:
    wallet_file = Path(forced)
else:
    candidates = WalletDiscovery(root).scan()
    if not candidates:
        raise SystemExit("ERROR: no existing wallet candidate found")
    wallet_file = Path(candidates[0]["path"])

adapter = ExistingWalletAdapter(wallet_file)
connector = CryptoPaymentConnector(adapter)
health = connector.health()

config = {
    "wallet_file": str(wallet_file),
    "health": health,
}
cfg = root / ".companyos_runtime" / "crypto_wallet_binding.json"
cfg.parent.mkdir(parents=True, exist_ok=True)
cfg.write_text(json.dumps(config, indent=2), encoding="utf-8")

print(json.dumps({
    "success": bool(health.get("success")),
    "status": "existing_wallet_bound" if health.get("success") else "wallet_found_but_adapter_incomplete",
    "wallet_file": str(wallet_file),
    "health": health,
    "note": "No private key material was read or printed by this binder."
}, indent=2))
