from datetime import datetime,timezone
from .customer_engine import CustomerEngine
from .sales_pipeline import SalesPipeline
from .finance_controller import FinanceController
from .execution_scheduler import ExecutionScheduler
from .competitive_intelligence import CompetitiveIntelligence
from .scale_engine import ScaleEngine
class CompanyOrchestrator:
    """84: company-level internal operating cycle."""
    def __init__(self):
        self.customer=CustomerEngine(); self.sales=SalesPipeline(); self.finance=FinanceController()
        self.scheduler=ExecutionScheduler(); self.competitive=CompetitiveIntelligence(); self.scale=ScaleEngine()
    def run(self,p):
        return {"success":True,"status":"phase84_company_cycle_completed",
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "customers":self.customer.segment(p.get("customer_signals",[])),
        "sales":self.sales.forecast(p.get("deals",[])),
        "finance":self.finance.assess(p.get("cash",0),p.get("monthly_burn",0),p.get("planned_spend",0)),
        "ready_tasks":self.scheduler.ready(p.get("tasks",[]),p.get("completed",[])),
        "competition":self.competitive.gaps(p.get("our_features",[]),p.get("competitors",[])),
        "scale":self.scale.evaluate(p.get("kpis",{})),"external_action_taken":False}
