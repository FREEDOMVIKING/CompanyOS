from companyos_phase1101_1250 import SalesPipelineEngine,CashflowGuard,BusinessRiskGate

def test_sales_score():
    l={"pain_confirmed":True,"budget_confirmed":True}
    assert SalesPipelineEngine().score_lead(l)==50

def test_cash_guard():
    f={"free_cash":10000,"runway_months":12}
    assert CashflowGuard().evaluate(f,1000)["allowed"] is True

def test_risk_gate():
    assert BusinessRiskGate().evaluate("hire_employee")["requires_approval"] is True
