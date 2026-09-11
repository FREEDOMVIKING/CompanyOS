class RevalidationPolicy:
    """852: bounded revalidation loops."""
    def next(self, decision, attempts, max_attempts=3):
        attempts=int(attempts)
        if decision=="REVISE" and attempts < max_attempts:
            return {"revalidate":True,"next_attempt":attempts+1}
        return {"revalidate":False,"next_attempt":attempts}
