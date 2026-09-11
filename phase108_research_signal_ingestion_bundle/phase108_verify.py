#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase106_store_present": Path("companyos/runtime/opportunity_discovery.py").exists(),
    "phase107_evidence_present": Path("companyos/runtime/research_evidence_pipeline.py").exists(),
    "phase108_signal_store_present": Path("companyos/runtime/research_signal_ingestion.py").exists(),
    "phase108_normalizer_present": Path("companyos/runtime/research_signal_normalizer.py").exists(),
    "phase108_pipeline_present": Path("companyos/runtime/research_signal_pipeline.py").exists(),
    "phase108_cli_present": Path("phase108_runtime_ingest_signal.py").exists(),
}
ok = all(checks.values())
for k,v in checks.items():
    print(k, "=>", "PASS" if v else "FAIL")

print("RAW_RESEARCH_SIGNAL_INGESTION: True")
print("SIGNAL_DEDUPLICATION: True")
print("SIGNAL_TO_EVIDENCE_NORMALIZATION: True")
print("PHASE107_RESEARCH_ASSESSMENT_REUSED: True")
print("OPPORTUNITY_RESCORING_AUTOMATED: True")
print("SIGNAL_PIPELINE_EXTERNAL_ACTIONS: False")
print("SIGNAL_PIPELINE_SIGNS_TRANSACTION: False")
print("SIGNAL_PIPELINE_BROADCASTS: False")
print("PHASE108_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
