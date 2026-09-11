from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
files = [
    ROOT/"companyos/strategy/orchestration_candidate_extractor_v2.py",
    ROOT/"scripts/companyos_orchestration_candidate_extractor_v2.py",
    ROOT/"scripts/companyos_extract_then_rank_profit_first.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.strategy.orchestration_candidate_extractor_v2 import extract_for_orchestration
r = extract_for_orchestration()
if "orchestration_id" not in r and r.get("reason") != "no_traced_orchestration_id":
    raise SystemExit("VERIFY_FAIL: malformed extraction result")

print("ORCHESTRATION_CANDIDATE_EXTRACTOR_V2_VERIFY: PASS")
print("ORCHESTRATION_ID:", r.get("orchestration_id"))
print("RAW_FOUND:", r.get("raw_candidate_objects_found"))
print("DEDUP_FOUND:", r.get("deduplicated_candidates_found"))
print("FILES_WRITTEN_OR_REPAIRED:", r.get("candidate_files_written_or_repaired"))
