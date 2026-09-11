from pathlib import Path
import py_compile
ROOT=Path.home()/"companyos"
files=[
    ROOT/"companyos/strategy/diversified_opportunity_governor.py",
    ROOT/"companyos/runtime/productive_autonomy_watchdog.py",
]
for p in files:
    print(p,"=>","PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p),doraise=True)

from companyos.strategy.diversified_opportunity_governor import state_snapshot, discovery_directive
print(state_snapshot())
print(discovery_directive()[:3000])
print("DIVERSIFIED_OPPORTUNITY_PORTFOLIO_VERIFY: PASS")
