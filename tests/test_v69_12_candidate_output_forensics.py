import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"audit/COMPANYOS_V69_12_CANDIDATE_OUTPUT_FORENSICS.json"

def report():
    return json.loads(REPORT.read_text())

def test_forensic_parser_control_passes():
    d=report()
    assert d["parser_control"]["looks_like_candidate"] is True
    assert d["parser_control"]["normalized_by_materializer"] is True

def test_forensics_found_completed_orchestrations():
    d=report()
    assert d["recent_completed_orchestration_count"] > 0
    assert d["completed_stage_tasks_inspected"] > 0

def test_runtime_root_topology_is_recorded():
    d=report()
    r=d["runtime_roots"]
    assert r["autonomous_task_queue_root"]
    assert r["default_specialist_evidence_root"]
    assert r["candidate_materialization_runtime"]
    assert r["research_output_capture_runtime"]

def test_forensics_are_read_only():
    d=report()
    assert d["runtime_files_modified"] is False
    assert d["external_actions_performed"] is False
    assert d["financial_actions_performed"] is False
    assert d["email_actions_performed"] is False
    assert d["deployment_actions_performed"] is False
