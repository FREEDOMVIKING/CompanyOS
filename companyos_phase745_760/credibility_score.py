class CredibilityScore:
    """751: source credibility weighting by source class and authority."""
    BASE = {
        "official":1.0,
        "official_docs":1.0,
        "official_sources":1.0,
        "primary_research":0.95,
        "reputable_news":0.85,
        "github":0.75,
        "competitor_site":0.7,
        "public_web":0.6,
        "hacker_news":0.45,
        "unknown":0.35,
    }
    def score(self, item):
        cls = item.get("source_class","unknown")
        base = self.BASE.get(cls, 0.35)
        if item.get("authoritative"): base += 0.05
        if item.get("anonymous"): base -= 0.1
        return round(max(0.0,min(1.0,base)),3)
