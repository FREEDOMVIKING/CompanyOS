from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads(
        (ROOT/"audit/COMPANYOS_V69_1_ADAPTIVE_THROUGHPUT_BENCHMARK.json").read_text()
    )

def test_v69_1_overall_passes():
    assert report()["overall_status"]=="PASS"

def test_backpressure_threshold_matrix_passes():
    d=report()["synthetic_backpressure_matrix"]
    assert d["pass"] is True
    assert all(x["pass"] for x in d["cases"])

def test_dispatch_policy_boosts_largest_type_and_oldest_within_type():
    d=report()["synthetic_dispatch_policy"]
    assert d["pass"] is True
    assert d["largest_type_boost_verified"] is True
    assert d["oldest_within_boost_verified"] is True

def test_real_queue_makes_progress_when_supported_work_exists():
    d=report()["actual_internal_queue_benchmark"]
    before=d["before"]
    if before["supported_due"]>0:
        assert d["total_dispatched"]>0
        assert d["completed_delta"]>0
    assert d["failed_delta"]<=0

def test_benchmark_performed_no_external_actions():
    d=report()
    assert d["external_actions_performed"] is False
    assert d["financial_actions_performed"] is False
    assert d["email_actions_performed"] is False
    assert d["deployment_actions_performed"] is False
