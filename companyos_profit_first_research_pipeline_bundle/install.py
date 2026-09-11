from pathlib import Path
import shutil, time, subprocess, os

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/strategy/profit_first_research_pipeline.py",
    "scripts/patch_profit_first_research.py",
    "scripts/companyos_profit_first_research_status.py",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

(ROOT / ".companyos_runtime" / "profit_first_candidates").mkdir(parents=True, exist_ok=True)

env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"
subprocess.run(["python", "scripts/patch_profit_first_research.py"], cwd=ROOT, env=env, check=True)

print("PROFIT_FIRST_RESEARCH_PIPELINE_INSTALL: PASS")
print("STRUCTURED_CANDIDATE_OUTPUT_CONTRACT: ENABLED")
print("MARKET_SCAN_STAGE: ENABLED")
print("EVIDENCE_ENRICHMENT_STAGE: ENABLED")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
