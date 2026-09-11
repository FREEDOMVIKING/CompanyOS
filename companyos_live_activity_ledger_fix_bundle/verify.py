from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
files = [
    ROOT / "dashboard" / "autonomy_activity_ledger_server.py",
    ROOT / "dashboard" / "autonomy_activity_ledger.html",
    ROOT / "dashboard" / "autonomy_activity_ledger_start.sh",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")

py_compile.compile(str(ROOT / "dashboard" / "autonomy_activity_ledger_server.py"), doraise=True)

print("LIVE_AUTONOMY_ACTIVITY_LEDGER_VERIFY: PASS")
