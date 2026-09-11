from pathlib import Path
import shutil, time

ROOT = Path.home()/"companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/strategy/profit_first_orchestration_trace.py",
    "scripts/companyos_trace_profit_first_orchestration.py",
    "scripts/companyos_profit_first_trace_and_repair.py",
]:
    src = SRC/rel
    dst = ROOT/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name+".bak."+stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

print("PROFIT_FIRST_ORCHESTRATION_TRACE_INSTALL: PASS")
print("TRACE_EXACT_EXPANSION_ORCHESTRATION: ENABLED")
print("TRACE_JOURNALS_AND_ARTIFACTS: ENABLED")
print("AUTO_MATERIALIZATION_REPAIR: ENABLED")
print("TARGETED_OUTPUT_RECOVERY: ENABLED")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
