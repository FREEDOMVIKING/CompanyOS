from .expansion_radar import ExpansionRadar
from .market_entry import MarketEntryPlanner
from .venture_replication import VentureReplicationEngine
from .shared_services import SharedServicesAllocator
from .cross_venture_sales import CrossVentureSalesEngine
from .cross_sell_engine import CrossSellEngine
from .regionalization import RegionalizationPlanner
from .partner_engine import PartnerOpportunityEngine
from .portfolio_synergy import PortfolioSynergyEngine
from .expansion_risk import ExpansionRiskEngine
from .expansion_sequencer import ExpansionSequencer
from .authority_boundary import ExpansionAuthorityBoundary
from .state_store import ExpansionState
from .audit import ExpansionAudit

class CEOExpansionOpsController:
    def __init__(self,root):
        self.state=ExpansionState(root)
        self.audit=ExpansionAudit(root)

    def run(self, opportunities=None, ventures=None, services=None, customers=None,
            customer_portfolio=None, venture_offers=None, partners=None, actions=None):
        ranked=ExpansionRadar().rank(opportunities or [])
        risked=[]
        for o in ranked:
            risk=ExpansionRiskEngine().evaluate(o)
            risked.append({**o,**risk})
        sequenced=ExpansionSequencer().sequence(risked)

        top=sequenced[0] if sequenced else None
        market_entry=MarketEntryPlanner().plan(top) if top else None
        replication=None
        if top and ventures:
            replication=VentureReplicationEngine().replicate(ventures[0],top.get("market","new_market"))

        shared=SharedServicesAllocator().allocate(ventures or [],services or [])
        sales=CrossVentureSalesEngine().match(customers or [],ventures or [])
        cross_sell=CrossSellEngine().recommend(customer_portfolio or {},venture_offers or [])
        partners_ranked=PartnerOpportunityEngine().rank(partners or [])
        synergies=PortfolioSynergyEngine().evaluate(ventures or [])
        boundaries=[{**a,**ExpansionAuthorityBoundary().evaluate(a)} for a in (actions or [])]

        result={
            "success":True,
            "status":"autonomous_multi_venture_expansion_cycle_complete",
            "ranked_expansion_opportunities":ranked,
            "risk_adjusted_sequence":sequenced,
            "market_entry_plan":market_entry,
            "venture_replication":replication,
            "shared_services":shared,
            "cross_venture_sales":sales,
            "cross_sell_recommendations":cross_sell,
            "partner_opportunities":partners_ranked,
            "portfolio_synergies":synergies,
            "authority_boundaries":boundaries
        }
        self.state.save(result)
        self.audit.append("expansion_cycle",result)
        return result
