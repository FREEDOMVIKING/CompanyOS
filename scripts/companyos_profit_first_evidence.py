import json
from companyos.strategy.profit_first_evidence_pipeline import build_evidence_report

r = build_evidence_report()
print(json.dumps({
    "candidate_count": r["candidate_count"],
    "sector_count": r["sector_count"],
    "business_model_count": r["business_model_count"],
    "research_requirements_met": r["research_requirements_met"],
    "qualified_count": r["ranking"].get("qualified_count", 0),
    "selected_for_validation": [
        {
            "name": x.get("name"),
            "sector": x.get("sector"),
            "business_model": x.get("business_model"),
            "profit_first_score": x.get("profit_first_score"),
        }
        for x in r["ranking"].get("selected_for_validation", [])
    ],
    "build_authorized_by_profit_engine": r["ranking"].get("build_authorized_by_profit_engine"),
    "no_build_reason": r["ranking"].get("no_build_reason"),
    "report_path": ".companyos_runtime/profit_first_evidence_report.json",
}, indent=2, default=str))
