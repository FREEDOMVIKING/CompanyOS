from companyos.runtime.post_launch_revenue_loop import PostLaunchRevenueLoop
def test_no_fake_metrics(tmp_path):
    r=PostLaunchRevenueLoop(tmp_path)
    e=r.collect_public_evidence({})
    assert e["revenue"] is None and e["leads"] is None and e["conversions"] is None and e["traffic"] is None
def test_unreachable_improves(tmp_path):
    r=PostLaunchRevenueLoop(tmp_path)
    d=r.decide({"status":"launched"},{"site_reachable":False})
    assert d["decision"]=="improve"
def test_unknown_market_data_holds(tmp_path):
    r=PostLaunchRevenueLoop(tmp_path)
    d=r.decide({"status":"launched"},{"site_reachable":True,"revenue":None,"conversions":None})
    assert d["decision"]=="hold" and "evidence" in d["reason"]
def test_observed_revenue_scales(tmp_path):
    r=PostLaunchRevenueLoop(tmp_path)
    d=r.decide({"status":"launched"},{"site_reachable":True,"revenue":25,"conversions":1})
    assert d["decision"]=="scale"
