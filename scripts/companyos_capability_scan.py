#!/usr/bin/env python3
import json
from pathlib import Path

root = Path.home() / "companyos"
capabilities = set()

for p in root.rglob("*.py"):
    parts = set(p.parts)
    if ".git" in parts or "__pycache__" in parts or "backups" in parts:
        continue
    name = p.stem.lower()
    if name in {"research","market_scan","analysis","coding","engineering","quality","release",
                "deployment","marketing","operations","customer_success","communications",
                "finance","accounting","revenueops","strategy","planning","project_management",
                "portfolio_review","memory","ceo","verification"}:
        capabilities.add(name)

print(json.dumps({
    "success": True,
    "status": "capability_scan_complete",
    "count": len(capabilities),
    "capabilities": sorted(capabilities)
}, indent=2))
