from companyos_phase905_920 import SignalQualityRanker
class SignalQualityFilter:
    """925: keep decision-useful evidence from adaptive recovery."""
    def apply(self, evidence, min_quality=0.6):
        ranked=SignalQualityRanker().rank(evidence or [])
        kept=[e for e in ranked if float(e.get("signal_quality",0))>=float(min_quality)]
        dropped=[e for e in ranked if e not in kept]
        return {"kept":kept,"dropped":dropped}
