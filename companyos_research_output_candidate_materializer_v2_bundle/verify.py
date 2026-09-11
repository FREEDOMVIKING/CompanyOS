from pathlib import Path
import py_compile

ROOT = Path.home()/"companyos"
files = [
    ROOT/"companyos/strategy/research_output_candidate_materializer_v2.py",
    ROOT/"scripts/companyos_research_output_candidate_materializer_v2.py",
    ROOT/"scripts/companyos_materialize_v2_then_rank.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.strategy.research_output_candidate_materializer_v2 import materialize_all
r = materialize_all()
if "raw_capture_file_count" not in r or "candidate_objects_found" not in r:
    raise SystemExit("VERIFY_FAIL: malformed result")

print("RESEARCH_OUTPUT_CANDIDATE_MATERIALIZER_V2_VERIFY: PASS")
print("RAW_CAPTURE_FILES:", r["raw_capture_file_count"])
print("CANDIDATE_OBJECTS_FOUND:", r["candidate_objects_found"])
print("FILES_WRITTEN_OR_REPAIRED:", r["candidate_files_written_or_repaired"])
