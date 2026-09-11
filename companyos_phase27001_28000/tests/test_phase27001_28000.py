from companyos.businessops import VentureEngine, PortfolioPolicy

def test_ranking():
    r = VentureEngine().select([
        {"name":"a","expected_value":10,"confidence":1,"risk":0,"effort":0},
        {"name":"b","expected_value":5,"confidence":1,"risk":0,"effort":0}
    ])
    assert r[0]["name"] == "a"

def test_kill_decision():
    p = PortfolioPolicy().decide({"revenue":0,"cost":50,"profit":-50})
    assert p["action"] == "review_or_kill"
