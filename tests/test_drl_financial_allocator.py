from companyos.runtime import advanced_drl_controller as drl

def test_capital_action_exists():
    assert "allocate_verified_capital" in drl.ACTIONS

def test_action_space_unique():
    assert len(drl.ACTIONS)==len(set(drl.ACTIONS))
