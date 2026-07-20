class InitiativeFactory:
    """166: create initiatives automatically from goals, gaps, and evidence."""
    def create(self, goals, gaps):
        rows=[]
        for i,g in enumerate(goals):
            rows.append({"id":f"goal-{i+1}","source":"goal","initiative":g,"status":"queued","autonomous":True})
        for i,g in enumerate(gaps):
            rows.append({"id":f"gap-{i+1}","source":"gap","initiative":f"resolve:{g}","status":"queued","autonomous":True})
        return rows
