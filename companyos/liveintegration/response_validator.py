class ResponseValidator:
    def validate(self, response, required_fields=None):
        missing=[f for f in (required_fields or []) if f not in (response or {})]
        return {
            "valid":bool(response is not None) and not missing,
            "missing_fields":missing,
            "success":bool((response or {}).get("success",False))
        }
