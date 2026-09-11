class CompletionPolicy:
    """787: decide when multi-provider research is complete."""
    def decide(self, confidence, diversity_passed, completeness, provider_chain_exhausted=False):
        if float(confidence) >= 0.7 and diversity_passed and completeness:
            return {"complete":True,"reason":"quality_threshold_met"}
        if provider_chain_exhausted:
            return {"complete":True,"reason":"provider_chain_exhausted_partial_result"}
        return {"complete":False,"reason":"continue_collection"}
