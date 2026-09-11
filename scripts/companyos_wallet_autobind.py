#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.walletautobind import ExistingWalletLocator, WalletBindingWriter

root = Path.home() / "companyos"
locator = ExistingWalletLocator(root)
best = locator.best()

if not best:
    print(json.dumps({
        "success":False,
        "status":"no_wallet_candidate_found"
    }, indent=2))
    raise SystemExit(1)

result = WalletBindingWriter(root).write(
    best,
    metadata={
        "binding_mode":"autodiscovered_existing_wallet",
        "private_keys_copied":False
    }
)
print(json.dumps(result, indent=2))
