from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads(
        (ROOT/"audit/COMPANYOS_V69_7_POST_LOAD_DRAIN_FORENSICS.json").read_text()
    )

def test_injected_backlog_fully_drained():
    d=report()
    assert d["final_snapshot"]["injected"]["queued"]==0
    assert d["final_snapshot"]["injected"]["running"]==0
    assert d["final_snapshot"]["injected"]["failed"]==0
    assert d["injected_drain_seconds_after_load"] is not None

def test_supervisor_stayed_stable():
    d=report()
    assert d["max_restart_total"]==0
    assert d["max_consecutive_failures"]==0
    assert d["signal9_hits"]==0
    assert d["force_kill_hits"]==0
    assert d["memory_error_hits"]==0

def test_queue_remained_bounded():
    d=report()
    assert d["max_total_queued"]<=1000
    assert d["final_snapshot"]["native"]["queued"]<=400

def test_forensics_are_isolated():
    d=report()
    assert d["real_companyos_runtime_modified"] is False
    assert d["real_companyos_queue_modified"] is False
    assert d["external_actions_performed"] is False
    assert d["financial_actions_performed"] is False
    assert d["email_actions_performed"] is False
    assert d["deployment_actions_performed"] is False
