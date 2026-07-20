from datetime import datetime,timezone
from .hypothesis_manager import HypothesisManager
from .market_model import MarketModel
from .product_portfolio import ProductPortfolio
from .customer_success import CustomerSuccess
from .cashflow_planner import CashflowPlanner
from .compliance_gate import ComplianceGate
from .autonomy_budget import AutonomyBudget
class CompanyOperatingSystem:
    """124: integrated company operating cycle with bounded autonomy."""
    def __init__(self):
        self.h=HypothesisManager();self.market=MarketModel();self.products=ProductPortfolio()
        self.customers=CustomerSuccess();self.cash=CashflowPlanner();self.compliance=ComplianceGate();self.budget=AutonomyBudget()
    def run(self,p):
        return {"success":True,"status":"phase124_company_operating_cycle_completed","timestamp":datetime.now(timezone.utc).isoformat(),
        "hypotheses":self.h.rank(p.get("hypotheses",[])),
        "market":self.market.estimate(p.get("total_customers",0),p.get("annual_value",0),p.get("serviceable_pct",0),p.get("obtainable_pct",0)),
        "products":self.products.review(p.get("products",[])),"customers":self.customers.analyze(p.get("customers",[])),
        "cashflow":self.cash.project(p.get("starting_cash",0),p.get("monthly_inflows",[]),p.get("monthly_outflows",[])),
        "compliance":[{**a,"gate":self.compliance.evaluate(a)} for a in p.get("actions",[])],
        "autonomy_budget":self.budget.check(p.get("autonomy_used",0),p.get("autonomy_limit",0),p.get("autonomy_requested",0)),
        "external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False}
