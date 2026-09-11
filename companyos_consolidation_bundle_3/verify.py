from pathlib import Path
import json
from companyos.canonicalruntime import UnifiedCEOCanonicalBridge

root = Path.home() / "companyos"

checks = {
    "bundle1": (root/"companyos"/"canonicalexec"/"gateway.py").exists(),
    "bundle2": (root/"companyos"/"canonicalorchestration"/"bridge.py").exists(),
    "bundle3": (root/"companyos"/"canonicalruntime"/"bridge.py").exists(),
    "cli": (root/"scripts"/"companyos_canonical_runtime.py").exists(),
}

status = UnifiedCEOCanonicalBridge().status()
checks["status"] = status

print(json.dumps(checks, indent=2, sort_keys=True))

ok = all(checks[k] for k in ["bundle1","bundle2","bundle3","cli"]) and status.get("ready")
print("BUNDLE3_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
