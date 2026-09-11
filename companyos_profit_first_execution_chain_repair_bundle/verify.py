from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
files = [
    ROOT/"companyos/strategy/profit_first_execution_chain_repair.py",
    ROOT/"scripts/companyos_profit_first_execution_chain_repair.py",
    ROOT/"scripts/companyos_profit_first_execution_chain_status.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.strategy.profit_first_execution_chain_repair import FANOUT_BATCHES, batch_goal
if len(FANOUT_BATCHES) < 7:
    raise SystemExit("VERIFY_FAIL: insufficient fanout batches")
g = batch_goal(FANOUT_BATCHES[0])
checks = [
    ".companyos_runtime/profit_first_candidates/" in g,
    "at least 4 materially distinct venture candidates" in g,
    "Numeric scores are 0-100" in g,
    "Do not create renamed/versioned variants" in g,
]
for i, ok in enumerate(checks, 1):
    print(f"CHECK_{i}:", "PASS" if ok else "FAIL")
if not all(checks):
    raise SystemExit("VERIFY_FAIL: contract missing")

print("PROFIT_FIRST_EXECUTION_CHAIN_REPAIR_VERIFY: PASS")
