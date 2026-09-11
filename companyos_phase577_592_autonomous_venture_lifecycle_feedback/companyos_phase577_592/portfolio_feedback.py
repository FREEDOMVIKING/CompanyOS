class PortfolioFeedback:
    """588: compare venture progress and flag where CEO attention should move."""

    def analyze(self, records):
        ranked = sorted(
            records,
            key=lambda r: (
                float(r.get("last_outcome_score",0)),
                float((r.get("evidence") or {}).get("retention_rate",0)),
                float((r.get("evidence") or {}).get("revenue_signal",0)),
            ),
            reverse=True,
        )
        return {
            "ranked_venture_ids":[r.get("venture_id") for r in ranked],
            "top_venture":ranked[0].get("venture_id") if ranked else None,
            "attention_rule":"favor_progressing_ventures_and_research_stagnant_ones",
        }
