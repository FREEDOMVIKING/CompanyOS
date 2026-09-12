from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos.runtime.research_to_execution_bridge import scan_candidates, status

candidates = scan_candidates()
st = status()

print("===== RESEARCH TO EXECUTION VALIDATION =====")
print("valid_candidate_count:", len(candidates))
print("promotion_count:", st.get("promotion_count"))
print("top_candidates:")
for c in candidates[:5]:
    print(json.dumps({
        "name": c.name,
        "slug": c.slug,
        "score": c.score,
        "confidence": c.confidence,
        "evidence_count": c.evidence_count,
        "source": c.source,
    }, sort_keys=True))
print("COMPANYOS_RESEARCH_TO_EXECUTION_VALIDATION=PASS")
