#!/usr/bin/env python3
from pathlib import Path
import json
import time

roots = {
    "policy_audit": Path.home() / ".companyos_runtime" / "execution_audit",
    "live_control": Path.home() / ".companyos_runtime" / "live_execution_control",
    "lifecycle": Path.home() / ".companyos_runtime" / "transaction_lifecycle",
}

print("=== COMPANYOS LIVE EXECUTION STATUS ===")
for name, root in roots.items():
    print()
    print(name.upper())
    print("PATH:", root)
    if not root.exists():
        print("STATUS: NO DATA")
        continue

    files = sorted(root.rglob("*.json"))
    print("RECORDS:", len(files))
    for p in files[-5:]:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if name == "live_control":
            print(
                d.get("reason"),
                "| live=", d.get("live_requested"),
                "| allowed=", d.get("allowed"),
            )
        elif name == "policy_audit":
            print(
                d.get("event_type"),
                "| reason=", d.get("reason"),
                "| signature=", "YES" if d.get("signature") else "NO",
            )
        else:
            print(
                d.get("state"),
                "| destination=", d.get("destination"),
                "| signature=", "YES" if d.get("signature") else "NO",
            )
