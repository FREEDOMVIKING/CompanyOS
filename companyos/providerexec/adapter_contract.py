class AdapterContract:
    REQUIRED=("name","capabilities","execute")
    def validate(self, adapter):
        missing=[x for x in self.REQUIRED if not hasattr(adapter,x)]
        return {"valid":not missing,"missing":missing}
