from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads((ROOT/"audit/COMPANYOS_V69_0D_RUNTIME_AWARE_BASELINE.json").read_text())

def test_baseline_validation_passes():
    d=report()
    assert d["overall_status"]=="PASS"
    assert d["validation"]["full_pytest"]=="PASS"
    assert d["validation"]["runtime_health"]=="PASS"
    assert d["validation"]["launch_readiness"]=="PASS"

def test_runtime_was_live_during_validation():
    d=report()
    s=d["supervisor_validation_snapshot"]
    assert s["live_validation_evidence"] is True
    assert s["effective_supervisor_alive_during_validation"] is True
    assert s["service_count"]>0
    assert s["running_service_count"]>0
    assert d["validation"]["status_rc"]==0
    assert d["validation"]["runtime_health"]=="PASS"
    assert d["validation"]["launch_readiness"]=="PASS"

def test_consolidation_checkpoint_is_preserved():
    d=report()["consolidation"]
    assert d["v68_3c_present"] is True
    assert d["v68_4_present"] is True
    assert d["v68_5b_present"] is True
    assert d["canonical_workspace"]=="workspace/local_contractor_bid_organizer"
    assert d["progress_history_files_preserved"]>0
    assert d["progress_history_rewritten"] is False

def test_no_external_action_guards_changed():
    d=report()
    assert all(v is False for v in d["mutation_guards"].values())
