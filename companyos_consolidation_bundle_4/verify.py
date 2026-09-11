from pathlib import Path
import json
from companyos.canonicalproduction import CanonicalProductionRuntime

root = Path.home() / "companyos"
checks = {
    "bundle1": (root/"companyos"/"canonicalexec"/"gateway.py").exists(),
    "bundle2": (root/"companyos"/"canonicalorchestration"/"bridge.py").exists(),
    "bundle3": (root/"companyos"/"canonicalruntime"/"bridge.py").exists(),
    "bundle4": (root/"companyos"/"canonicalproduction"/"controller.py").exists(),
    "cli": (root/"scripts"/"companyos_master_runtime.py").exists(),
    "phase102_ctl": (root/"phase102_ceo_runtime_stack_integration_bundle"/"phase102_unified_runtime_ctl.py").exists(),
}

rt = CanonicalProductionRuntime()
status = rt.status()
checks["status"] = status

print(json.dumps(checks, indent=2, sort_keys=True))

ok = all(checks[k] for k in ["bundle1","bundle2","bundle3","bundle4","cli","phase102_ctl"])
print("BUNDLE4_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
