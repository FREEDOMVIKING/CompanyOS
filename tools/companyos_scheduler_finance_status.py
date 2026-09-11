#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
roots={
    "dispatcher": Path.home()/".companyos_runtime"/"scheduler_financial_dispatcher",
    "activity_ledger": Path.home()/".companyos_runtime"/"autonomy_activity_ledger",
    "bridge": Path.home()/".companyos_runtime"/"autonomous_financial_bridge",
}
print("=== SCHEDULER FINANCIAL STATUS ===")
for name,root in roots.items():
    fs=sorted(root.rglob("*.json")) if root.exists() else []
    print()
    print(name.upper(),"RECORDS:",len(fs))
    for p in fs[-5:]:
        try:d=json.loads(p.read_text())
        except Exception:continue
        if name=="dispatcher":
            r=d.get("result",{})
            print(r.get("action_id"),"|",r.get("requested_mode"),"|",r.get("reason"),"| sig=","YES" if r.get("signature") else "NO")
        elif name=="activity_ledger":
            r=d.get("result",{})
            print(d.get("event_type"),"|",r.get("reason"),"| state=",r.get("state"),"| sig=","YES" if r.get("signature") else "NO")
        else:
            r=d.get("result",{})
            print(r.get("mode"),"|",r.get("reason"),"| sig=","YES" if r.get("signature") else "NO")
