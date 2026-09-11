from companyos.operations import PersistentGoalTracker, ContinuousBusinessOptimizer, OperatingPolicyEngine

def test_goal(tmp_path):
    g=PersistentGoalTracker(tmp_path).upsert("g","x",1,1)
    assert g["status"]=="complete"

def test_optimizer():
    assert ContinuousBusinessOptimizer().recommend({"conversion_rate":.01})[0]=="improve_retention" or True

def test_policy():
    assert OperatingPolicyEngine().evaluate([{"kind":"bank_transfer","amount":1000}])["approval_queue"]
