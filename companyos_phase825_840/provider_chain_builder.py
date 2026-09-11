from companyos_phase761_776 import FallbackCycle

class ProviderChainBuilder:
    """832: build escalation chain across providers."""

    def build(self, preferred, query_type="market", unavailable=None, max_providers=5):
        unavailable = set(unavailable or [])
        chain = []
        current = preferred

        for _ in range(max_providers):
            if current and current not in unavailable and current not in chain:
                chain.append(current)
            nxt = FallbackCycle().choose(current, query_type, unavailable | set(chain))
            if not nxt or nxt in chain:
                break
            current = nxt

        return chain
