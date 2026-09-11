from pathlib import Path
import json
from companyos.canonicaldaemon import CanonicalCompanyOSDaemon

root = Path.home() / "companyos"
checks = {
    "daemon_package": (root/"companyos"/"canonicaldaemon"/"daemon.py").exists(),
    "daemon_cli": (root/"scripts"/"companyos_canonical_daemon.py").exists(),
    "service_script": (root/"scripts"/"companyos_service.sh").exists(),
    "autostart_ready": (root/"scripts"/"companyos_autostart_ready.sh").exists(),
    "bundle4": (root/"companyos"/"canonicalproduction"/"controller.py").exists(),
}
print(json.dumps(checks, indent=2, sort_keys=True))
ok = all(checks.values())
print("BUNDLE5_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
