class IntegrationValidator:
    def validate(self, interfaces):
        missing=[]
        broken=[]
        for i in interfaces or []:
            if not i.get("source") or not i.get("target"):
                broken.append(i)
            if not i.get("contract"):
                missing.append(i)
        return {"valid":not broken and not missing,"broken":broken,"missing_contracts":missing}
