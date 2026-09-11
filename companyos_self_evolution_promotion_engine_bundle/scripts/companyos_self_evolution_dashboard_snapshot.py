import json
from pathlib import Path
from companyos.evolution.self_evolution_promotion_engine import ledger, load, STATE

ROOT = Path.home()/"companyos"
rows = ledger(100)
payload = {
    "summary": {
        "promoted": sum(1 for x in rows if x.get("status") == "PROMOTED"),
        "rolled_back": sum(1 for x in rows if x.get("status") == "ROLLED_BACK"),
        "rejected": sum(1 for x in rows if str(x.get("status", "")).startswith("REJECTED")),
        "awaiting_approval": sum(1 for x in rows if x.get("status") == "AWAITING_APPROVAL"),
    },
    "state": load(STATE, {}),
    "recent": rows[-25:],
}
out = ROOT/".companyos_runtime/self_evolution/dashboard_snapshot.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2, default=str)+"\n", encoding="utf-8")
print(json.dumps(payload, indent=2, default=str))
