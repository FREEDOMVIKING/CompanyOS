from .financial_planner import FinancialPlanner
from .cashflow_engine import CashflowEngine
from .runway_manager import RunwayManager
from .scale_allocator import ScaleAllocator
from .vendor_manager import VendorManager
from .compliance_registry import ComplianceRegistry
from .risk_register import RiskRegister
from .governance_engine import GovernanceEngine
from .scenario_planner import ScenarioPlanner
from .capital_efficiency import CapitalEfficiencyEngine
from .portfolio_rebalancer import PortfolioRebalancer
from .approval_matrix import ApprovalMatrix
from .state_store import ScaleOpsState
from .audit import ScaleOpsAudit

class CEOScaleOpsController:
    def __init__(self,root):
        self.state=ScaleOpsState(root)
        self.audit=ScaleOpsAudit(root)

    def run(self, finance=None, opportunities=None, vendors=None, obligations=None, compliance_evidence=None,
            risks=None, decisions=None, scenarios=None, ventures=None, actions=None):
        f=finance or {}
        financials=FinancialPlanner().plan(
            f.get("revenue",0),f.get("cogs",0),f.get("opex",0),f.get("growth_investment",0)
        )
        cash=CashflowEngine().evaluate(f.get("opening_cash",0),f.get("inflows",0),f.get("outflows",0))
        burn=max(0,float(f.get("outflows",0))-float(f.get("inflows",0)))
        runway=RunwayManager().compute(cash["closing_cash"],burn)
        scale=ScaleAllocator().allocate(opportunities or [],f.get("scale_budget",0))
        vendor_rank=VendorManager().evaluate(vendors or [])
        compliance=ComplianceRegistry().evaluate(obligations or [],compliance_evidence or [])
        risk_rank=RiskRegister().prioritize(risks or [])
        governance=GovernanceEngine().review(decisions or [])
        scenario=ScenarioPlanner().run(
            (scenarios or {}).get("base",{}),
            (scenarios or {}).get("upside",{}),
            (scenarios or {}).get("downside",{})
        )
        efficiency=CapitalEfficiencyEngine().evaluate(
            f.get("revenue_growth",0),max(1,burn),financials.get("gross_margin",0)
        )
        rebalance=PortfolioRebalancer().rebalance(ventures or [])
        routing=ApprovalMatrix().route(actions or [])
        result={
            "success":True,
            "status":"autonomous_finance_compliance_scale_cycle_complete",
            "financials":financials,
            "cashflow":cash,
            "runway":runway,
            "scale_allocations":scale,
            "vendor_ranking":vendor_rank,
            "compliance":compliance,
            "risk_register":risk_rank,
            "governance_review":governance,
            "scenario_plan":scenario,
            "capital_efficiency":efficiency,
            "portfolio_rebalancing":rebalance,
            **routing
        }
        self.state.save(result)
        self.audit.append("scale_ops_cycle",result)
        return result
