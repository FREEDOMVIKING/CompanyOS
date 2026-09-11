from companyos_phase561_576 import VentureScorecard, CommitmentGate, KillScalePolicy

def test_scorecard():
    s=VentureScorecard().score({"validation_score":8,"activation_rate":0.3,"retention_rate":0.3,"revenue_signal":4})
    assert s["score"]>0

def test_commitment_gate():
    e={"validation_decision":"go_to_mvp","validation_score":7}
    assert CommitmentGate().evaluate("validation",e)["commitment_allowed"] is True

def test_scale_policy():
    d=KillScalePolicy().decide({"validation_score":8,"activation_rate":0.3,"retention_rate":0.35,"revenue_signal":4})
    assert d["decision"]=="scale"
