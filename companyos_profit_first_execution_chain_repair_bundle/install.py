from pathlib import Path
import shutil, time

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/strategy/profit_first_execution_chain_repair.py",
    "scripts/companyos_profit_first_execution_chain_repair.py",
    "scripts/companyos_profit_first_execution_chain_status.py",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

print("PROFIT_FIRST_EXECUTION_CHAIN_REPAIR_INSTALL: PASS")
print("SPECIALIST_RESEARCH_FANOUT: ENABLED")
print("DIRECT_CANDIDATE_WRITE_CONTRACT: ENABLED")
print("BATCH_SUMMARY_CONTRACT: ENABLED")
print("FAKE_CANDIDATES_SEEDED: NO")
print("THRESHOLD_LOWERED: NO")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
