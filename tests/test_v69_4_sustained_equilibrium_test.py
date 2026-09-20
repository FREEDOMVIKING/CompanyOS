from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads(
        (ROOT/"audit/COMPANYOS_V69_4_SUSTAINED_EQUILIBRIUM_TEST.json").read_text()
    )

def test_v69_4_overall_passes():
    assert report()["overall_status"]=="PASS"

def test_sustainable_load_remains_bounded():
    d=report()["sustainable_load"]
    assert d["pass"] is True
    assert d["producer_allowed_ticks"]>0
    assert d["producer_blocked_ticks"]>0
    assert d["final"]["failed"]==0
    assert d["final"]["queued"]<=d["producer_burst"]
    assert d["max_queued_after_production"]<=200
    assert d["max_queued_after_execution"]<=128

def test_overload_activates_hard_stop_and_stays_bounded():
    d=report()["overload_recovery"]
    assert d["pass"] is True
    assert d["hard_stop_ticks"]>0
    assert d["producer_blocked_ticks"]>0
    assert d["max_queue"]<=500
    assert d["end_load"]["queued"]<=400
    assert d["end_load"]["failed"]==0

def test_recovery_drains_to_zero():
    d=report()["overload_recovery"]
    assert d["recovery_ticks_used"]<=d["recovery_ticks_budget"]
    assert d["final"]["queued"]==0
    assert d["final"]["failed"]==0

def test_no_external_or_real_queue_actions():
    d=report()
    assert d["real_companyos_queue_modified"] is False
    assert d["external_actions_performed"] is False
    assert d["financial_actions_performed"] is False
    assert d["email_actions_performed"] is False
    assert d["deployment_actions_performed"] is False
