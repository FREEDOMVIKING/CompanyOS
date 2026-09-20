from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads((ROOT/"audit/COMPANYOS_V69_8_NATIVE_GOAL_LINEAGE.json").read_text())

def test_native_task_creation_is_bounded():
    d=report()
    f=d["final_lineage"]
    assert d["max_native_queued"]<=300
    assert f["root_goal_count"]<=12
    assert f["states"].get("FAILED",0)==0

def test_native_goal_shape_is_consistent():
    d=report()
    assert d["three_stage_goal_shape_pass"] is True
    assert d["final_lineage"]["malformed_goal_sets"]==[]
    assert d["final_lineage"]["orphan_goal_tasks"]==0

def test_followup_depth_guard_holds():
    d=report()
    assert d["followup_depth_guard_pass"] is True

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
