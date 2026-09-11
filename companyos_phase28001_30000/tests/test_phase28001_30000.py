from companyos.autonomy import AutonomyGovernor
def test_safe_autonomy():
    assert AutonomyGovernor().classify({"external":False})["decision"]=="autonomous_allowed"
def test_irreversible_gate():
    assert AutonomyGovernor().classify({"irreversible":True})["decision"]=="approval_required"
