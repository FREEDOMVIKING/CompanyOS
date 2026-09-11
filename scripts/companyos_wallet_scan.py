#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.cryptoops import WalletDiscovery

root = Path.home() / "companyos"
results = WalletDiscovery(root).scan()
print(json.dumps({
    "success": True,
    "status": "wallet_scan_complete",
    "count": len(results),
    "candidates": results[:25]
}, indent=2))
