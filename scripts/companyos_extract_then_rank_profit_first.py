import json
from companyos.strategy.orchestration_candidate_extractor_v2 import extract_for_orchestration
from companyos.strategy.profit_first_evidence_pipeline import build_evidence_report

print("===== EXTRACT =====")
x = extract_for_orchestration()
print(json.dumps(x, indent=2, default=str))

print("===== EVIDENCE =====")
e = build_evidence_report()
print(json.dumps({
    "candidate_count": e.get("candidate_count"),
    "sector_count": e.get("sector_count"),
    "business_model_count": e.get("business_model_count"),
    "qualified_count": (e.get("ranking") or {}).get("qualified_count"),
    "selected_for_validation": (e.get("ranking") or {}).get("selected_for_validation"),
}, indent=2, default=str))
