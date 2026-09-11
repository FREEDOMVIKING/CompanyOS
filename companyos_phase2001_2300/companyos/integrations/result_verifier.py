class ResultVerifier:
    def verify(self, result, required_fields=None):
        required_fields=list(required_fields or [])
        missing=[f for f in required_fields if f not in (result or {})]
        success=bool((result or {}).get("success",True)) and not missing
        return {"verified":success,"missing_fields":missing,"result":result}
