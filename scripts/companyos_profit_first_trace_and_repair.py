import json
from companyos.strategy.profit_first_orchestration_trace import trace
from companyos.strategy.candidate_materialization_bridge import materialize, maybe_recover_missing_outputs

before = trace()
print("===== TRACE BEFORE =====")
print(json.dumps(before.get("diagnosis", {}), indent=2))

status = (before.get("diagnosis") or {}).get("status")

if status == "research_output_exists_but_not_materialized":
    m = materialize()
    print("===== MATERIALIZATION =====")
    print(json.dumps(m, indent=2, default=str))
elif status == "orchestration_completed_without_traceable_output":
    r = maybe_recover_missing_outputs(min_expected_candidates=20, cooldown_seconds=0)
    print("===== TARGETED RECOVERY =====")
    print(json.dumps(r, indent=2, default=str))
else:
    print("===== NO REPAIR NEEDED =====")

after = trace()
print("===== TRACE AFTER =====")
print(json.dumps({
    "candidate_file_count_total": after.get("candidate_file_count_total"),
    "candidate_files_tied_to_orchestration": after.get("candidate_files_tied_to_orchestration"),
    "evidence_summary": after.get("evidence_summary"),
    "diagnosis": after.get("diagnosis"),
}, indent=2, default=str))
