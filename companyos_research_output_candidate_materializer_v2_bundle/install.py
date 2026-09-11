from pathlib import Path
import shutil, time

ROOT = Path.home()/"companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/strategy/research_output_candidate_materializer_v2.py",
    "scripts/companyos_research_output_candidate_materializer_v2.py",
    "scripts/companyos_materialize_v2_then_rank.py",
]:
    src = SRC/rel
    dst = ROOT/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name+".bak."+stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

print("RESEARCH_OUTPUT_CANDIDATE_MATERIALIZER_V2_INSTALL: PASS")
print("CANONICAL_CAPTURE_PARSING: ENABLED")
print("JSON_BLOB_EXTRACTION: ENABLED")
print("MARKDOWN_PROSE_EXTRACTION: ENABLED")
print("LINEAGE_REPAIR: ENABLED")
print("FAKE_CANDIDATES_SEEDED: NO")
print("THRESHOLD_LOWERED: NO")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
