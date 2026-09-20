from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads((ROOT/"audit/COMPANYOS_V69_9_NATIVE_PRODUCER_PROVENANCE.json").read_text())

def test_provenance_instrumentation_is_healthy():
    d=report()
    assert d["instrumentation_failures"]==[]
    assert d["goal_decompose_event_count"]>=d["ceo_start_event_count"]

def test_native_work_remains_bounded():
    d=report()
    assert d["max_native_queued"]<=300
    assert d["final_task_counts"]["states"].get("FAILED",0)==0

def test_runtime_stayed_stable():
    d=report()
    assert d["max_restart_total"]==0
    assert d["max_consecutive_failures"]==0
    assert d["signal9_hits"]==0
    assert d["force_kill_hits"]==0
    assert d["memory_error_hits"]==0

def test_forensics_were_isolated():
    d=report()
    assert d["real_companyos_runtime_modified"] is False
    assert d["real_companyos_queue_modified"] is False
    assert d["external_actions_performed"] is False
    assert d["financial_actions_performed"] is False
    assert d["email_actions_performed"] is False
    assert d["deployment_actions_performed"] is False
