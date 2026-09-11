from companyos_phase465_480 import StageRouter, FailureRecovery, CEORuntime

def test_router_validation_go():
    result = {"success":True,"data":{"decision":{"decision":"go_to_mvp"}}}
    assert StageRouter().next_stage("validation", result) == "venture"

def test_failure_recovery():
    assert FailureRecovery().decide(1,"build")["action"] == "retry_stage"
    assert FailureRecovery().decide(3,"build")["action"] == "pause_cycle"

def test_runtime():
    assert CEORuntime().status()["status"] == "phase480_persistent_ceo_operating_loop_ready"
