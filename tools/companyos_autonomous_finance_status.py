#!/usr/bin/env python3
from pathlib import Path
import json

root=Path.home()/".companyos_runtime"/"autonomous_financial_bridge"
print("=== AUTONOMOUS FINANCIAL BRIDGE STATUS ===")
print("PATH:", root)
if not root.exists():
    print("RECORDS: 0")
    raise SystemExit(0)

files=sorted(root.rglob("*.json"))
print("RECORDS:", len(files))
for p in files[-10:]:
    try:
        d=json.loads(p.read_text())
        a=d.get("action",{})
        r=d.get("result",{})
        print(
            a.get("action_id"),
            "|", r.get("mode"),
            "| accepted=", r.get("accepted"),
            "| reason=", r.get("reason"),
            "| state=", r.get("state"),
            "| signature=", "YES" if r.get("signature") else "NO",
        )
    except Exception:
        pass
