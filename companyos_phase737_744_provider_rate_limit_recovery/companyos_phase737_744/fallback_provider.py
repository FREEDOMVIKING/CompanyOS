class FallbackProvider:
    ORDER=["github","hacker_news","public_web","local_cache"]
    def choose(self,current_provider,unavailable=None):
        unavailable=set(unavailable or [])
        for p in self.ORDER:
            if p!=current_provider and p not in unavailable: return p
        return "local_cache"
