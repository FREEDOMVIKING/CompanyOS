class AutonomyBudget:
    """123: cap autonomous internal resource use by mission."""
    def check(self,used,limit,requested):
        used=max(0,float(used));limit=max(0,float(limit));requested=max(0,float(requested))
        allowed=used+requested<=limit
        return {"used":used,"limit":limit,"requested":requested,"allowed":allowed,
        "remaining":round(max(0,limit-used),4)}
