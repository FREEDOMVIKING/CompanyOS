from companyos.scaleops import FinancialPlanner, RunwayManager, ApprovalMatrix

def test_finance():
    assert FinancialPlanner().plan(1000,200,300)["gross_profit"]==800.0

def test_runway():
    assert RunwayManager().compute(1200,100)["runway_months"]==12.0

def test_approval():
    assert ApprovalMatrix().route([{"kind":"contract_signature"}])["approval_queue"]
