from __future__ import annotations

class MarketGapDetector:
    """343: infer candidate gaps from pain density and competitor pressure."""

    def detect(self, clusters, competitor_signals):
        pressure = len(competitor_signals)
        gaps = []
        for cluster in clusters:
            count = int(cluster.get("count", 0))
            if count <= 0:
                continue
            gaps.append({
                "theme": cluster.get("theme"),
                "pain_evidence_count": count,
                "competitor_signal_count": pressure,
                "gap_strength": round(count / max(1, pressure + 1), 3),
                "needs_validation": True,
            })
        return sorted(gaps, key=lambda x: x["gap_strength"], reverse=True)
