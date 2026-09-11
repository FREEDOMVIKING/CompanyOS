from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
files = [
    ROOT/"companyos"/"runtime"/"productive_autonomy_watchdog.py",
    ROOT/"scripts"/"companyos_productive_autonomy.sh",
    ROOT/"scripts"/"companyos_final_launch_fixed.sh",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
py_compile.compile(str(ROOT/"companyos"/"runtime"/"productive_autonomy_watchdog.py"), doraise=True)
print("PRODUCTIVE_AUTONOMY_VERIFY: PASS")
