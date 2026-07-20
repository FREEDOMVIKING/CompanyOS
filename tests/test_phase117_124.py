from companyos_phase117_124 import CashflowPlanner,ComplianceGate,AutonomyBudget
def test_cashflow_planning_only(): assert CashflowPlanner().project(10,[1],[1])["funds_moved"] is False
def test_compliance_blocks_unreviewed(): assert ComplianceGate().evaluate({"category":"financial_transaction"})["allowed"] is False
def test_autonomy_budget_cap(): assert AutonomyBudget().check(9,10,2)["allowed"] is False
