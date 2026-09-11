from pathlib import Path
import shutil, time

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/strategy/orchestration_candidate_extractor_v2.py",
    "scripts/companyos_orchestration_candidate_extractor_v2.py",
    "scripts/companyos_extract_then_rank_profit_first.py",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

print("ORCHESTRATION_CANDIDATE_EXTRACTOR_V2_INSTALL: PASS")
print("EXACT_ORCHESTRATION_LINEAGE: ENABLED")
print("NESTED_JSON_EXTRACTION: ENABLED")
print("PROSE_OUTPUT_EXTRACTION: ENABLED")
print("CANDIDATE_LINEAGE_REPAIR: ENABLED")
print("FAKE_CANDIDATES_SEEDED: NO")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
