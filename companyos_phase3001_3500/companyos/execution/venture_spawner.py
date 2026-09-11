import uuid

class VentureSpawner:
    def spawn(self, thesis, evidence=None, budget_cap=500):
        return {
            "venture_id":"venture_"+uuid.uuid4().hex[:10],
            "thesis":thesis,
            "evidence":list(evidence or []),
            "stage":"discover",
            "budget_cap":float(budget_cap),
            "status":"active",
        }
