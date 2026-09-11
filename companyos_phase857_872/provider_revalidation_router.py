class ProviderRevalidationRouter:
    def route(self,task,provider_health=None):
        health=provider_health or {}
        preferred=["official","public_web","reputable_news","github"]
        available=[p for p in preferred if health.get(p,{}).get("available",True)]
        return {"task":task,"provider_chain":available or ["public_web"],"fallback_enabled":True}
