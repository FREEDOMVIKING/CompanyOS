from __future__ import annotations
from .customer_pain_filter import CustomerPainFilter
from .developer_demand_filter import DeveloperDemandFilter
from .signal_quality import SignalQuality

class DiscoveryInputBuilder:
    """364: filter/dedupe-ish public signals into evidence for Phase 301-352."""

    def __init__(self):
        self.pain = CustomerPainFilter()
        self.demand = DeveloperDemandFilter()
        self.quality = SignalQuality()

    def build(self, records, min_quality=5):
        painful = self.pain.apply(records)
        demanded = self.demand.apply(painful)
        out, seen = [], set()
        for r in demanded:
            key = (r.get("url") or "", r.get("title") or "")
            if key in seen:
                continue
            seen.add(key)
            score = self.quality.score(r)
            if score >= int(min_quality):
                out.append({**r, "public_signal_quality": score})
        return out
