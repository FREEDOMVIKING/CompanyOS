from .business_ops_state import BusinessOpsState
from .customer_acquisition import CustomerAcquisitionEngine
from .sales_pipeline import SalesPipelineEngine
from .offer_optimizer import OfferOptimizer
from .campaign_allocator import CampaignAllocator
from .crm_orchestrator import CRMOrchestrator
from .customer_success import CustomerSuccessEngine
from .financial_controller import FinancialController
from .cashflow_guard import CashflowGuard
from .resource_allocator import ResourceAllocator
from .kpi_engine import KPIEngine
from .growth_experiment_loop import GrowthExperimentLoop
from .portfolio_orchestrator import PortfolioOrchestrator
from .business_risk_gate import BusinessRiskGate
from .business_audit import BusinessAudit

class CEOBusinessOpsController:
    """1249: unified autonomous business operations and portfolio controller."""
    def __init__(self,root):
        self.root=root
        self.state=BusinessOpsState(root)
        self.audit=BusinessAudit(root)

    def run(self, venture_id, channels=None, acquisition_budget=0, leads=None, offers=None,
            campaigns=None, customers=None, finance=None, kpis=None, growth_experiments=None,
            growth_results=None, portfolio_ventures=None):

        finance=finance or {}
        financials=FinancialController().compute(
            finance.get("cash",0),finance.get("revenue",0),finance.get("cogs",0),
            finance.get("opex",0),finance.get("committed_spend",0)
        )

        spend_guard=CashflowGuard().evaluate(financials,acquisition_budget)

        acquisition = (
            CustomerAcquisitionEngine().plan(channels or [], acquisition_budget, finance.get("target_cac"))
            if spend_guard["allowed"]
            else {"selected_channels":[],"blocked":True,"reason":spend_guard["reason"]}
        )

        sales=SalesPipelineEngine().process(leads or [])
        offer=OfferOptimizer().recommend(offers or [])
        allocations=CampaignAllocator().allocate(campaigns or [], acquisition_budget if spend_guard["allowed"] else 0)
        crm=CRMOrchestrator().actions(sales)
        cs=CustomerSuccessEngine().evaluate(customers or [])
        kpi=KPIEngine().score(kpis or {})
        experiments=GrowthExperimentLoop().select(growth_experiments or [])
        learnings=GrowthExperimentLoop().evaluate(growth_results or [])
        portfolio=PortfolioOrchestrator().decide(portfolio_ventures or [])

        risk_examples={
            "large_marketing_spend":BusinessRiskGate().evaluate("large_marketing_spend",acquisition_budget),
            "contract_signature":BusinessRiskGate().evaluate("contract_signature",0),
        }

        result={
            "success":True,
            "status":"autonomous_business_ops_cycle_complete",
            "venture_id":venture_id,
            "financials":financials,
            "spend_guard":spend_guard,
            "acquisition":acquisition,
            "sales_pipeline":sales,
            "offer_optimization":offer,
            "campaign_allocations":allocations,
            "crm_actions":crm,
            "customer_success":cs,
            "kpi":kpi,
            "growth_experiments":experiments,
            "growth_learnings":learnings,
            "portfolio_decisions":portfolio,
            "risk_gates":risk_examples,
        }

        self.state.save(venture_id,result)
        self.audit.append(result)
        return result
