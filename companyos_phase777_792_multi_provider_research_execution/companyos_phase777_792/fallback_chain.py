from companyos_phase761_776 import FallbackCycle
class FallbackChain:
    """780: build ordered provider chain starting with preferred provider."""
    def build(self, preferred, query_type, unavailable=None, max_providers=4):
        unavailable=set(unavailable or [])
        chain=[]
        current=preferred
        for _ in range(max_providers):
            if current and current not in chain and current not in unavailable:
                chain.append(current)
            nxt=FallbackCycle().choose(current, query_type, unavailable | set(chain))
            if not nxt or nxt in chain:
                break
            current=nxt
        return chain
