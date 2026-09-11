class AdaptiveExecutionHealth:
    """935: summarize adaptive execution health."""
    def evaluate(self,result):
        return {"healthy":bool((result or {}).get("success")),
                "raw_evidence_count":int((result or {}).get("raw_evidence_count",0)),
                "accepted_evidence_count":len((result or {}).get("accepted_evidence",[]) or []),
                "decision":((result or {}).get("decision") or {}).get("decision")}
