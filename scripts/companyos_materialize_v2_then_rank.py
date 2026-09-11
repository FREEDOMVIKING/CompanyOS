import json
from companyos.strategy.research_output_candidate_materializer_v2 import materialize_all
from companyos.strategy.profit_first_evidence_pipeline import build_evidence_report

print("===== MATERIALIZE V2 =====")
m = materialize_all()
print(json.dumps(m, indent=2, default=str))

print("===== EVIDENCE =====")
e = build_evidence_report()
print(json.dumps({
    "candidate_count": e.get("candidate_count"),
    "sector_count": e.get("sector_count"),
    "business_model_count": e.get("business_model_count"),
    "qualified_count": (e.get("ranking") or {}).get("qualified_count"),
    "selected_for_validation": (e.get("ranking") or {}).get("selected_for_validation"),
    "build_authorized_by_profit_engine": (e.get("ranking") or {}).get("build_authorized_by_profit_engine"),
}, indent=2, default=str))
