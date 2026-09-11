class PortfolioActionPolicy:
    """680: recommend spin-up, pause, merge, kill, maintain, or scale."""

    def decide(self, venture):
        score=float(venture.get("portfolio_score",0))
        stagnant=int(venture.get("stagnant_cycles",0))
        duplicate=bool(venture.get("duplicate_risk"))
        profitable=bool(venture.get("profitable"))
        if duplicate and score < 5:
            action="merge_or_cancel"
        elif stagnant >= 3 and score < 4:
            action="pause_or_kill"
        elif score >= 8 and profitable:
            action="scale"
        elif score >= 5:
            action="maintain_or_iterate"
        else:
            action="research_more"
        return {"decision":action}
