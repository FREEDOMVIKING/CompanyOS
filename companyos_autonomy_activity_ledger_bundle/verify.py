from pathlib import Path
import py_compile
ROOT=Path.home()/"companyos"
for p in [ROOT/"dashboard"/"autonomy_activity_ledger_server.py",ROOT/"dashboard"/"autonomy_activity_ledger.html",ROOT/"dashboard"/"autonomy_activity_ledger_start.sh"]:
    print(p,"=>","PASS" if p.exists() else "FAIL")
    if not p.exists(): raise SystemExit("VERIFY_FAIL")
py_compile.compile(str(ROOT/"dashboard"/"autonomy_activity_ledger_server.py"),doraise=True)
print("AUTONOMY_ACTIVITY_LEDGER_VERIFY: PASS")
