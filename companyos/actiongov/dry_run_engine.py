class DryRunEngine:
    def simulate(self, action):
        return {
            "action":action,
            "simulated":True,
            "predicted_effects":{
                "external_change":bool(action.get("external",True)),
                "financial_delta":-float(action.get("amount",0) or 0),
                "reversible":bool(action.get("reversible",False))
            }
        }
