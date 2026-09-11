class ResearchCycleHealth:
    """774: health evaluation for research cycles."""
    def evaluate(self,result):
        q=(result or {}).get("quality") or {}
        packet=q.get("packet") or {}
        return {
            "healthy":bool(result.get("success")),
            "decision":result.get("decision"),
            "confidence":packet.get("confidence",0),
            "provider":result.get("selected_provider"),
            "retry_remaining":result.get("retry_remaining",0),
        }
