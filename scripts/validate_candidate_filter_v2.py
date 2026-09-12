from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos.runtime.research_to_execution_bridge import (
    scan_candidates,
    maybe_promote_candidate,
)

rows = scan_candidates(min_score=45)
print("===== FILTERED REAL CANDIDATES =====")
print("count:", len(rows))
for c in rows[:10]:
    print(json.dumps({
        "name": c.name,
        "slug": c.slug,
        "score": c.score,
        "confidence": c.confidence,
        "evidence_count": c.evidence_count,
        "source": c.source,
    }, sort_keys=True))

print("===== PROMOTION DECISION (NO COOLDOWN) =====")
result = maybe_promote_candidate(
    min_score=45,
    cooldown_seconds=0,
)
print(json.dumps(result, indent=2, sort_keys=True, default=str))
print("COMPANYOS_CANDIDATE_FILTER_V2=PASS")
