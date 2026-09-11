class ProviderMixOptimizer:
    """908: avoid repeating the same provider mix after weak rounds."""
    def optimize(self, previous_providers=None, causes=None):
        previous=set(previous_providers or [])
        preferred=["official","reputable_news","public_web","github","hacker_news"]
        ranked=[p for p in preferred if p not in previous] + [p for p in preferred if p in previous]
        if "low_source_diversity" in set((causes or {}).get("reasons",[])):
            ranked=["official","reputable_news","hacker_news","public_web","github"]
        return ranked
