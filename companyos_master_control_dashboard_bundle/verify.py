from pathlib import Path
import py_compile
ROOT=Path.home()/"companyos"
for p in [ROOT/"dashboard"/"master_control_server.py",ROOT/"dashboard"/"master_control.html",ROOT/"dashboard"/"master_control_start.sh"]:
    print(p,"=>","PASS" if p.exists() else "FAIL")
    if not p.exists(): raise SystemExit("VERIFY_FAIL")
py_compile.compile(str(ROOT/"dashboard"/"master_control_server.py"),doraise=True)
print("MASTER_CONTROL_VERIFY: PASS")
