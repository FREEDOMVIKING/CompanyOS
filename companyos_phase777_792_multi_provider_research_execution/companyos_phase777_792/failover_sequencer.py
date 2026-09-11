class FailoverSequencer:
    """784: decide whether to continue to next provider."""
    def next(self, index, chain, normalized_error, evidence_count, target_min=3):
        if evidence_count >= target_min:
            return {"continue":False,"reason":"minimum_evidence_reached"}
        if index + 1 >= len(chain):
            return {"continue":False,"reason":"provider_chain_exhausted"}
        if normalized_error.get("retryable"):
            return {"continue":True,"reason":"retryable_provider_failure"}
        return {"continue":True,"reason":"insufficient_evidence"}
