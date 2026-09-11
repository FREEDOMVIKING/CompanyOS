from pathlib import Path
import json
from companyos.canonicalexec import CanonicalExecutionGateway
root=Path.home()/"companyos"
checks={
 "package_present":(root/"companyos"/"canonicalexec"/"gateway.py").exists(),
 "cli_present":(root/"scripts"/"companyos_execution_gateway.py").exists(),
}
checks["status"]=CanonicalExecutionGateway().status()
print(json.dumps(checks, indent=2, sort_keys=True))
ok=checks["package_present"] and checks["cli_present"] and checks["status"].get("ready")
print("BUNDLE1_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
