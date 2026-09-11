class RevalidationRoundScheduler:
    """889: decide whether another autonomous revalidation round should run."""
    def next_round(self, current_round, decision, max_rounds=3):
        current_round=int(current_round)
        if decision in ("GO","KILL"):
            return {"run":False,"reason":f"terminal_{decision.lower()}","next_round":current_round}
        if current_round>=int(max_rounds):
            return {"run":False,"reason":"max_rounds_reached","next_round":current_round}
        return {"run":True,"reason":"continue_revalidation","next_round":current_round+1}
