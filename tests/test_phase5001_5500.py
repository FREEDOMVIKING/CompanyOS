from companyos.growthops import MarketRadar, OpportunityRanker, GrowthApprovalRouter
def test_market():
    assert MarketRadar().scan([{"demand":1,"growth":1,"urgency":1,"competition":0}])[0]["market_score"]==1
def test_rank():
    assert OpportunityRanker().rank([{"value":1,"confidence":1,"speed":1,"effort":1,"risk":0}])[0]["priority_score"]==1
def test_gate():
    assert GrowthApprovalRouter().route([{"kind":"contract_signature"}])["approval_queue"]
