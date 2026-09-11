from pathlib import Path
import py_compile

ROOT = Path.home()/"companyos"
files = [
    ROOT/"companyos/strategy/profit_first_orchestration_trace.py",
    ROOT/"scripts/companyos_trace_profit_first_orchestration.py",
    ROOT/"scripts/companyos_profit_first_trace_and_repair.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.strategy.profit_first_orchestration_trace import trace
r = trace()
if "diagnosis" not in r:
    raise SystemExit("VERIFY_FAIL: diagnosis missing")

print("PROFIT_FIRST_ORCHESTRATION_TRACE_VERIFY: PASS")
print("TRACE_STATUS:", (r.get("diagnosis") or {}).get("status"))
