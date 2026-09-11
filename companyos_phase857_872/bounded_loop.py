class BoundedRevalidationLoop:
    def evaluate(self,attempt,decision,stagnant,max_attempts=3):
        if decision in ("GO","KILL"): return {"continue":False,"reason":f"terminal_{decision.lower()}"}
        if stagnant: return {"continue":False,"reason":"stagnation_detected"}
        if int(attempt)>=int(max_attempts): return {"continue":False,"reason":"max_attempts_reached"}
        return {"continue":True,"reason":"revalidation_required","next_attempt":int(attempt)+1}
