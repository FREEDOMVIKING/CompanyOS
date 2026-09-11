from companyos.marketops import MarketSignalEngine, PricingEngine, MarketOpsGuardrails

def test_signal():
    assert MarketSignalEngine().score([{"demand":1,"pain":1,"urgency":1,"budget":1,"competition_gap":1,"evidence_quality":1}])[0]["market_score"]>.9

def test_pricing():
    assert PricingEngine().recommend([{"name":"x","price":100,"conversion_rate":.1,"retention_rate":.8,"gross_margin":.8}])["winner"]["name"]=="x"

def test_guardrails():
    assert MarketOpsGuardrails().route([{"kind":"bank_transfer","amount":1000}])["approval_queue"]
