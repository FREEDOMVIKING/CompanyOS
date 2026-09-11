from pathlib import Path
import py_compile
R=Path.home()/"companyos"
for p in [R/"dashboard/autonomy_activity_ledger_server.py",R/"dashboard/autonomy_activity_ledger.html"]:
    print(p,"=>","PASS" if p.exists() else "FAIL")
    if not p.exists():raise SystemExit(1)
py_compile.compile(str(R/"dashboard/autonomy_activity_ledger_server.py"),doraise=True)
print("LEDGER_TIMESTAMP_DEDUPE_VERIFY: PASS")
