from pathlib import Path
import py_compile

ROOT = Path.home()/"companyos"
files = [
    ROOT/"companyos/strategy/profit_first_evidence_pipeline.py",
    ROOT/"scripts/companyos_profit_first_evidence.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")

py_compile.compile(str(files[0]), doraise=True)
py_compile.compile(str(files[1]), doraise=True)

from companyos.strategy.profit_first_evidence_pipeline import build_evidence_report
r = build_evidence_report()
if "ranking" not in r:
    raise SystemExit("VERIFY_FAIL: ranking missing")

print("PROFIT_FIRST_EVIDENCE_PIPELINE_VERIFY: PASS")
print("CANDIDATES_FOUND:", r["candidate_count"])
print("SECTORS_FOUND:", r["sector_count"])
print("BUSINESS_MODELS_FOUND:", r["business_model_count"])
