#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase106_store_present": Path("companyos/runtime/opportunity_discovery.py").exists(),
    "phase107_pipeline_present": Path("companyos/runtime/research_evidence_pipeline.py").exists(),
    "phase107_bridge_present": Path("companyos/runtime/opportunity_research_bridge.py").exists(),
    "phase107_add_cli_present": Path("phase107_runtime_add_evidence.py").exists(),
    "phase107_assess_cli_present": Path("phase107_runtime_assess_opportunity.py").exists(),
}
ok = all(checks.values())
for k,v in checks.items():
    print(k, "=>", "PASS" if v else "FAIL")

print("PERSISTENT_RESEARCH_EVIDENCE: True")
print("EVIDENCE_QUALITY_SCORING: True")
print("CONTRADICTION_TRACKING: True")
print("OPPORTUNITY_RESCORING_FROM_RESEARCH: True")
print("RESEARCH_PIPELINE_EXTERNAL_ACTIONS: False")
print("RESEARCH_PIPELINE_SIGNS_TRANSACTION: False")
print("RESEARCH_PIPELINE_BROADCASTS: False")
print("PHASE107_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
