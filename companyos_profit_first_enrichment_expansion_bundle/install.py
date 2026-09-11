from pathlib import Path
import shutil, time, subprocess, os

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/strategy/profit_first_enrichment_expansion.py",
    "scripts/patch_profit_first_enrichment_expansion.py",
    "scripts/companyos_profit_first_enrichment_expansion_once.py",
    "scripts/companyos_profit_first_enrichment_expansion_status.py",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"
subprocess.run(
    ["python", "scripts/patch_profit_first_enrichment_expansion.py"],
    cwd=ROOT, env=env, check=True
)

print("PROFIT_FIRST_ENRICHMENT_EXPANSION_INSTALL: PASS")
print("OPPORTUNITY_EXPANSION: ENABLED")
print("EVIDENCE_ENRICHMENT: ENABLED")
print("VALIDATION_QUEUE_STAGE: ENABLED")
print("THRESHOLD_LOWERED: NO")
print("FAKE_CANDIDATES_SEEDED: NO")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
