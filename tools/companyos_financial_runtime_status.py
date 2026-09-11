#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

roots = {
    "bridge": Path.home()/".companyos_runtime"/"autonomous_financial_bridge",
    "policy": Path.home()/".companyos_runtime"/"execution_audit",
    "live_control": Path.home()/".companyos_runtime"/"live_execution_control",
    "lifecycle": Path.home()/".companyos_runtime"/"transaction_lifecycle",
}

print("=== COMPANYOS FINANCIAL RUNTIME STATUS ===")
for name, root in roots.items():
    files = sorted(root.rglob("*.json")) if root.exists() else []
    print()
    print(name.upper(), "RECORDS:", len(files))
    for p in files[-3:]:
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if name == "bridge":
            r = d.get("result", {})
            print(r.get("mode"), "|", r.get("reason"), "| sig=", "YES" if r.get("signature") else "NO")
        elif name == "policy":
            print(d.get("event_type"), "|", d.get("reason"), "| sig=", "YES" if d.get("signature") else "NO")
        elif name == "live_control":
            print(d.get("reason"), "| live=", d.get("live_requested"), "| allowed=", d.get("allowed"))
        else:
            print(d.get("state"), "| sig=", "YES" if d.get("signature") else "NO")
