class HypothesisFactory:
    """190: create testable hypotheses from intents."""
    def create(self,intents):
        return [{"intent":x.get("intent"),"hypothesis":f"measurable_action_improves:{x.get('intent')}",
                 "success_metric":"evidence_gain","autonomous_test_design":True} for x in intents]
