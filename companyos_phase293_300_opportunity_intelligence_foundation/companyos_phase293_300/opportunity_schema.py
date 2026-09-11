class OpportunitySchema:
    REQUIRED = ["name","problem","customer","solution","revenue_model","evidence"]

    def normalize(self, data):
        data = dict(data or {})
        missing = [k for k in self.REQUIRED if not data.get(k)]
        return {"valid": not missing, "missing": missing, "opportunity": data}
