class ProgressGuard:
    """585: detect repeated loops with no stage or evidence progress."""

    def evaluate(self, record):
        stagnant = int(record.get("stagnant_cycles",0))
        score = float(record.get("last_outcome_score",0))
        if score <= 0.5:
            stagnant += 1
        else:
            stagnant = 0

        if stagnant >= 3:
            action = "pause_and_research"
        elif stagnant == 2:
            action = "change_strategy"
        else:
            action = "continue"

        return {"stagnant_cycles":stagnant,"action":action}
