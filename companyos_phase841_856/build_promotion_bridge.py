class BuildPromotionBridge:
    """855: create build mission when validation decision is GO."""
    def build(self, adapted, validation_result):
        if validation_result.get("decision")!="GO":
            return None
        ctx=dict((adapted or {}).get("context") or {})
        source=(adapted or {}).get("mission_id") or "validation"
        return {
            "mission_id":f"{source}_build",
            "mission_type":"build",
            "priority":0.95,
            "attempts":0,
            "blocked_on":[],
            "status":"queued",
            "context":{
                **ctx,
                "venture_id":(adapted or {}).get("venture_id"),
                "validation_result":validation_result,
                "objective":"build the smallest validated product that satisfies the proven customer/problem hypothesis",
            },
        }
