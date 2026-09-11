from pathlib import Path
import json
from companyos.canonicalorchestration import CanonicalOrchestrationBridge

root = Path.home() / "companyos"

checks = {
    "bundle1_gateway_present": (root/"companyos"/"canonicalexec"/"gateway.py").exists(),
    "package_present": (root/"companyos"/"canonicalorchestration"/"bridge.py").exists(),
    "cli_present": (root/"scripts"/"companyos_orchestration_bridge.py").exists(),
}

status = CanonicalOrchestrationBridge().status()
checks["status"] = status

print(json.dumps(checks, indent=2, sort_keys=True))

ok = (
    checks["bundle1_gateway_present"]
    and checks["package_present"]
    and checks["cli_present"]
    and status.get("ready")
    and status.get("gateway", {}).get("ready")
)

print("BUNDLE2_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
