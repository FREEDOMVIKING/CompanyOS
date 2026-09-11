from companyos.revenueops import UnitEconomicsEngine, RevenueAuthorityBoundary, RevenueForecastEngine
def test_economics():
    assert UnitEconomicsEngine().calculate(100,40,20,12)["ltv_cac"]==36
def test_boundary():
    assert RevenueAuthorityBoundary().evaluate({"kind":"large_ad_spend"})["requires_approval"]
def test_forecast():
    assert len(RevenueForecastEngine().forecast(1000,.1,3))==3
