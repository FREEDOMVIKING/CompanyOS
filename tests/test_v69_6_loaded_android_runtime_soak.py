from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads(
        (ROOT/"audit/COMPANYOS_V69_6_LOADED_ANDROID_RUNTIME_SOAK.json").read_text()
    )

def test_loaded_soak_has_no_blocking_failures():
    d=report()
    assert d["overall_status"] in {"PASS","PASS_WITH_WARNINGS"}
    assert d["blocking_failures"] == []

def test_supervisor_remained_stable_under_load():
    d=report()
    assert d["supervisor_alive_samples"] == d["samples_collected"]
    assert d["healthy_samples"] == d["samples_collected"]
    assert d["max_restart_total"] == 0
    assert d["max_consecutive_failures"] == 0
    assert d["running_service_count_min"] == d["service_count_max"]

def test_internal_workload_made_progress_without_failures():
    d=report()
    assert d["produced_total"] > 0
    assert d["completed_total"] > 0
    assert d["failed_total"] == 0
    assert d["max_queued_tasks"] <= 1000
    assert d["final_queue"]["queued"] <= 400

def test_no_signal9_or_memory_failure():
    d=report()
    assert d["signal9_hits"] == 0
    assert d["force_kill_hits"] == 0
    assert d["memory_error_hits"] == 0

def test_loaded_soak_was_isolated():
    d=report()
    assert d["real_companyos_runtime_modified"] is False
    assert d["real_companyos_queue_modified"] is False
    assert d["external_actions_performed"] is False
    assert d["financial_actions_performed"] is False
    assert d["email_actions_performed"] is False
    assert d["deployment_actions_performed"] is False
