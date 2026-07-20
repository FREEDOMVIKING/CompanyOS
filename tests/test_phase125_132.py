from companyos_phase125_132 import AuthorityModel, ExperimentBudget, LaunchController, SelfRepairEngine

def test_internal_action_auto_allowed():
    assert AuthorityModel().evaluate({"type":"internal_code_change"})["allowed"] is True

def test_high_impact_still_gated():
    assert AuthorityModel().evaluate({"type":"sign_contract"})["approval_required"] is True

def test_bounded_experiment_auto_allowed():
    assert ExperimentBudget().authorize(5,10,.1)["allowed"] is True

def test_local_launch_auto_allowed():
    assert LaunchController().evaluate({"scope":"local","reversible":True,"bounded":True})["autonomous_launch_allowed"] is True

def test_safe_self_repair_auto():
    assert SelfRepairEngine().plan({"kind":"syntax_error","attempts":0})["autonomous"] is True
