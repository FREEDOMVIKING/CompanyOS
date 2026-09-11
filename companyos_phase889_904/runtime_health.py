class MultiRoundRuntimeHealth:
    """903: health summary for multi-round execution."""
    def evaluate(self,result):
        return {
            "healthy":bool((result or {}).get("success")),
            "rounds_executed":int((result or {}).get("rounds_executed",0)),
            "terminal_decision":((result or {}).get("terminal") or {}).get("decision"),
            "has_handoff":bool((result or {}).get("handoff")),
        }
