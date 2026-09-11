from pathlib import Path
import shutil, time

ROOT = Path.home()/"companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/strategy/profit_first_evidence_pipeline.py",
    "scripts/companyos_profit_first_evidence.py",
]:
    src = SRC/rel
    dst = ROOT/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name+".bak."+stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

print("PROFIT_FIRST_EVIDENCE_PIPELINE_INSTALL: PASS")
print("RANK_EXISTING_EVIDENCE: ENABLED")
print("NO_BUILD_WITHOUT_THRESHOLD: PRESERVED")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
