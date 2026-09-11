from pathlib import Path
import json
from companyos.finallaunch import FinalLaunchController

root=Path.home()/"companyos"
checks={
 "final_package":(root/"companyos"/"finallaunch"/"controller.py").exists(),
 "final_cli":(root/"scripts"/"companyos_final_launch.py").exists(),
 "final_shell":(root/"scripts"/"companyos_final_launch.sh").exists(),
 "service":(root/"scripts"/"companyos_service.sh").exists(),
}
ctl=FinalLaunchController()
checks["profile"]=ctl.current_profile()
checks["preflight"]=ctl.preflight()
print(json.dumps(checks,indent=2,sort_keys=True))
ok=all(checks[k] for k in ["final_package","final_cli","final_shell","service"])
print("FINAL_HAUL_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
