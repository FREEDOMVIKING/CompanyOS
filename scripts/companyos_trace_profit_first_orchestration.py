import json, sys
from companyos.strategy.profit_first_orchestration_trace import trace

oid = sys.argv[1] if len(sys.argv) > 1 else None
r = trace(oid)
print(json.dumps({
    "orchestration_id": r.get("orchestration_id"),
    "journal_hit_count": r.get("journal_hit_count"),
    "artifact_hit_count": r.get("artifact_hit_count"),
    "candidate_file_count_total": r.get("candidate_file_count_total"),
    "candidate_files_tied_to_orchestration": r.get("candidate_files_tied_to_orchestration"),
    "evidence_summary": r.get("evidence_summary"),
    "diagnosis": r.get("diagnosis"),
    "report_path": ".companyos_runtime/profit_first_orchestration_trace_report.json",
}, indent=2, default=str))
