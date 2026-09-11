from companyos_phase745_760 import QueryRouter
from companyos_phase737_744 import FallbackProvider
class FallbackCycle:
    """766: choose next source using query-type routing and fallback order."""
    def choose(self,current_provider,query_type,unavailable=None):
        unavailable=set(unavailable or [])
        for p in QueryRouter().route(query_type):
            if p!=current_provider and p not in unavailable:
                return p
        return FallbackProvider().choose(current_provider,unavailable)
