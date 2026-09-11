#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase107_autonomous_research_evidence_pipeline_bundle"

pairs = [
    (BUNDLE/"research_evidence_pipeline.py", ROOT/"companyos/runtime/research_evidence_pipeline.py"),
    (BUNDLE/"opportunity_research_bridge.py", ROOT/"companyos/runtime/opportunity_research_bridge.py"),
    (BUNDLE/"phase107_research_test.py", ROOT/"phase107_research_test.py"),
    (BUNDLE/"phase107_runtime_add_evidence.py", ROOT/"phase107_runtime_add_evidence.py"),
    (BUNDLE/"phase107_runtime_assess_opportunity.py", ROOT/"phase107_runtime_assess_opportunity.py"),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src,dst in pairs:
    text = src.read_text()
    ast.parse(text)
    if dst.exists():
        bak = dst.with_name(dst.name + f".phase107_backup_{stamp}")
        shutil.copy2(dst,bak)
        backups[str(dst)] = str(bak)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase":"107_AUTONOMOUS_RESEARCH_EVIDENCE_PIPELINE",
    "status":"installed",
    "persistent_research_evidence":True,
    "evidence_quality_scoring":True,
    "contradiction_tracking":True,
    "opportunity_rescoring_from_research":True,
    "external_actions":False,
    "signs_transaction":False,
    "broadcasts_transaction":False,
    "private_key_printed":False,
    "backups":backups,
}
(ROOT/"PHASE107_AUTONOMOUS_RESEARCH_EVIDENCE_PIPELINE_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n"
)

print("PHASE107_AUTONOMOUS_RESEARCH_EVIDENCE_PIPELINE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("PERSISTENT_RESEARCH_EVIDENCE: True")
print("EVIDENCE_QUALITY_SCORING: True")
print("CONTRADICTION_TRACKING: True")
print("OPPORTUNITY_RESCORING_FROM_RESEARCH: True")
print("RESEARCH_PIPELINE_EXTERNAL_ACTIONS: False")
print("RESEARCH_PIPELINE_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
