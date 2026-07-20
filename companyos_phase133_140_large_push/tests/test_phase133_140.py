from companyos_phase133_140 import OpportunityHunter, ContinuousExecutor, SelfOptimizer, PortfolioExpander

def test_opportunity_ranking():
    rows = OpportunityHunter().discover([
        {"name":"a","demand":1,"urgency":1,"willingness_to_pay":1,"competition":0,"confidence":1},
        {"name":"b","demand":0,"urgency":0,"willingness_to_pay":0,"competition":1,"confidence":0},
    ])
    assert rows[0]["name"] == "a"

def test_executor_skips_unapproved():
    rows = ContinuousExecutor().next_batch([
        {"id":"x","approval_required":True,"approved":False}
    ])
    assert rows == []

def test_safe_optimizer_auto_applies():
    assert SelfOptimizer().evaluate({"kind":"internal_workflow","reversible":True,"bounded":True})["auto_apply"] is True

def test_portfolio_expansion():
    result = PortfolioExpander().decide([
        {"name":"x","status":"active","traction":.9,"margin":.8,"learning":.8}
    ], 3)
    assert result["autonomous_expansion_allowed"] is True
