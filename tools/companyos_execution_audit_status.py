#!/usr/bin/env python3
from pathlib import Path
import json
import time

root = Path.home() / ".companyos_runtime" / "execution_audit"
day = time.strftime("%Y-%m-%d")
day_dir = root / day

events = []
if day_dir.exists():
    for p in sorted(day_dir.glob("*.json")):
        try:
            events.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass

spent = sum(
    float(x.get("amount_sol") or 0.0)
    for x in events
    if x.get("event_type") == "transfer_finalized"
)

print("=== EXECUTION AUDIT STATUS ===")
print("TODAY:", day)
print("EVENT COUNT:", len(events))
print("FINALIZED OUTBOUND SOL:", spent)

for x in events[-10:]:
    print(
        x.get("event_type"),
        "|", x.get("reason"),
        "| amount_sol=", x.get("amount_sol"),
        "| signature=", "YES" if x.get("signature") else "NO",
    )
