from companyos.capabilityops import StageCapabilityRouter, ControlledAutonomyPolicy

def test_router():
    r = StageCapabilityRouter().resolve("build", {"coding"})
    assert r["capability"] == "coding"

def test_policy_allows_bounded_action():
    p = ControlledAutonomyPolicy().decide({"impact":"low","reversible":True})
    assert p["decision"] == "autonomous_allowed"

def test_policy_gates_irreversible():
    p = ControlledAutonomyPolicy().decide({"reversible":False})
    assert p["decision"] == "approval_required"
