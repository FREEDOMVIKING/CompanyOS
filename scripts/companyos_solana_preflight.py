#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.walletautobind import SolanaPreflightValidator, WalletActivationReadiness

root = Path.home() / "companyos"
preflight = SolanaPreflightValidator(root).validate()
readiness = WalletActivationReadiness(root).evaluate(preflight)

print(json.dumps({
    "success": True,
    "status":"solana_preflight_complete",
    "preflight":preflight,
    "readiness":readiness
}, indent=2))
