class PortfolioLearning:
    """602: derive cross-venture lessons for CEO policy."""

    def summarize(self, venture_records):
        winners = []
        stalled = []
        for r in venture_records:
            score = float(r.get("last_outcome_score",0))
            if score >= 4:
                winners.append(r.get("venture_id"))
            if int(r.get("stagnant_cycles",0)) >= 2:
                stalled.append(r.get("venture_id"))
        return {
            "progressing_ventures":winners,
            "stalled_ventures":stalled,
            "policy":"reinforce_progressing_patterns_and_research_stalled_assumptions",
        }
