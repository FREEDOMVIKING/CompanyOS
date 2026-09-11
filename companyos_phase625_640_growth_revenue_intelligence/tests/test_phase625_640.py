from companyos_phase625_640 import VanityGuard, UnitEconomics, GrowthDecision

def test_vanity_guard():
    assert VanityGuard().evaluate({"impressions":1000,"clicks":50})["vanity_only"] is True

def test_unit_economics():
    e=UnitEconomics().calculate({
        "acquisition_spend":100,"paying_customers":5,
        "average_revenue_per_account":100,"gross_margin_rate":0.8,
        "monthly_churn_rate":0.1
    })
    assert e["economics_positive"] is True

def test_growth_decision():
    d=GrowthDecision().decide(
        6,8,{"economics_positive":True},
        {"vanity_only":False}
    )
    assert d["decision"]=="prepare_scale_review"
