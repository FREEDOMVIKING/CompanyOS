from companyos.autonomyops import ObjectiveEngine, PriorityEngine, AutonomyOpsStatus

def test_objective():
    assert ObjectiveEngine().choose([])

def test_priority():
    r = PriorityEngine().rank([
        {"name":"high","value":1.0,"confidence":1.0,"urgency":1.0,"risk":0.0,"effort":0.0},
        {"name":"low","value":0.1,"confidence":0.1,"urgency":0.1,"risk":0.9,"effort":0.9}
    ])
    assert r[0]["name"] == "high"

def test_status():
    assert AutonomyOpsStatus().status()["success"] is True
