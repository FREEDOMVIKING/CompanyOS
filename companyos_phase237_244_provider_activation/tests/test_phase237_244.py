from companyos_phase237_244 import ConnectionContract, MissionSeed, HandoffReadiness

def test_contract_rejects_unsafe_path():
    r = ConnectionContract().validate({"files":{"../x.py":"x=1"}})
    assert r["valid"] is False

def test_mission_seed():
    m = MissionSeed().create()
    assert m["required_capabilities"] == ["internal_health_summary"]

def test_handoff_not_ready_without_probe():
    r = HandoffReadiness().evaluate({})
    assert r["ready"] is False
