from typing import Any, Dict
class LaunchPlanner:
    """72: prepare launch plans while preserving external-action gates."""
    def plan(self, product: Dict[str,Any], channel="controlled_test"):
        return {"product":product.get("name","unnamed"),"channel":channel,
        "steps":["final_validation","readiness_check","approval_check","controlled_launch","measure"],
        "requires_approval_before_external_launch":True,"external_action_taken":False}
