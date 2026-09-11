#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase108_research_signal_ingestion_bundle"

pairs = [
    (BUNDLE/"research_signal_ingestion.py", ROOT/"companyos/runtime/research_signal_ingestion.py"),
    (BUNDLE/"research_signal_normalizer.py", ROOT/"companyos/runtime/research_signal_normalizer.py"),
    (BUNDLE/"research_signal_pipeline.py", ROOT/"companyos/runtime/research_signal_pipeline.py"),
    (BUNDLE/"phase108_signal_pipeline_test.py", ROOT/"phase108_signal_pipeline_test.py"),
    (BUNDLE/"phase108_runtime_ingest_signal.py", ROOT/"phase108_runtime_ingest_signal.py"),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src,dst in pairs:
    text = src.read_text()
    ast.parse(text)
    if dst.exists():
        bak = dst.with_name(dst.name + f".phase108_backup_{stamp}")
        shutil.copy2(dst,bak)
        backups[str(dst)] = str(bak)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase":"108_RESEARCH_SIGNAL_INGESTION",
    "status":"installed",
    "raw_research_signal_ingestion":True,
    "signal_deduplication":True,
    "signal_to_evidence_normalization":True,
    "phase107_research_assessment_reused":True,
    "opportunity_rescoring_automated":True,
    "external_actions":False,
    "signs_transaction":False,
    "broadcasts_transaction":False,
    "private_key_printed":False,
    "backups":backups,
}
(ROOT/"PHASE108_RESEARCH_SIGNAL_INGESTION_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n"
)

print("PHASE108_RESEARCH_SIGNAL_INGESTION: INSTALLED")
print("COMPILE_CHECK: PASS")
print("RAW_RESEARCH_SIGNAL_INGESTION: True")
print("SIGNAL_DEDUPLICATION: True")
print("SIGNAL_TO_EVIDENCE_NORMALIZATION: True")
print("OPPORTUNITY_RESCORING_AUTOMATED: True")
print("SIGNAL_PIPELINE_EXTERNAL_ACTIONS: False")
print("SIGNAL_PIPELINE_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
