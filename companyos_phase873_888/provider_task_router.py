class ProviderTaskRouter:
    """874: prioritize providers by task dimension."""
    def route(self, task):
        dim=(task.get("task") or {}).get("dimension")
        if dim=="pricing_validation":
            chain=["official","public_web","reputable_news","github"]
        elif dim=="problem_evidence":
            chain=["public_web","reputable_news","official","github"]
        elif dim=="validation_confidence":
            chain=["official","public_web","reputable_news","github"]
        else:
            chain=list(task.get("provider_chain") or ["public_web","official","github"])
        x=dict(task); x["provider_chain"]=chain
        return x
