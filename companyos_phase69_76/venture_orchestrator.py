from datetime import datetime,timezone
from typing import Any, Dict
from .opportunity_pipeline import OpportunityPipeline
from .validation_engine import ValidationEngine
from .product_factory import ProductFactory
from .launch_planner import LaunchPlanner
from .revenue_engine import RevenueEngine
from .operations_controller import OperationsController
class VentureOrchestrator:
    """76: opportunity-to-launch internal venture orchestration."""
    def __init__(self):
        self.op=OpportunityPipeline(); self.val=ValidationEngine(); self.factory=ProductFactory()
        self.launch=LaunchPlanner(); self.rev=RevenueEngine(); self.ops=OperationsController()
    def run(self,payload:Dict[str,Any]):
        ranked=self.op.rank(payload.get("opportunities",[]))
        winner=ranked[0] if ranked else {}
        validation=self.val.validate(payload.get("evidence",[]))
        spec=self.factory.create_spec(winner) if winner else {}
        launch=self.launch.plan(spec) if spec else {}
        return {"success":True,"status":"phase76_venture_cycle_completed",
        "timestamp":datetime.now(timezone.utc).isoformat(),"ranked_opportunities":ranked,
        "validation":validation,"product_spec":spec,"launch_plan":launch,
        "revenue_scenarios":self.rev.scenarios(payload.get("price",0),payload.get("customer_scenarios",[1,10,100])),
        "operations":self.ops.assess(payload.get("systems",{})),"external_action_taken":False}
