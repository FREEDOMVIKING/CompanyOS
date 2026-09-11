from companyos_phase449_464 import LaunchReadiness, UnitEconomics, ScaleDecision

def test_launch_gate():
    result = LaunchReadiness().evaluate({
        "release_candidate_ready":True,
        "telemetry_ready":True,
        "rollback_ready":True,
        "support_path_ready":True,
    })
    assert result["ready"] is True
    assert result["automatic_irreversible_launch"] is False

def test_unit_economics():
    result = UnitEconomics().calculate({
        "cac":50,"arpa":100,"gross_margin":0.8,"monthly_churn":0.1
    })
    assert result["ltv_cac_ratio"] > 1

def test_scale_decision():
    decision = ScaleDecision().decide({
        "activation_rate":0.4,
        "gross_retention":0.8,
        "mrr_growth_rate":0.2,
        "ltv_cac_ratio":4,
        "sample_size":100,
    })
    assert decision["decision"] == "scale"
