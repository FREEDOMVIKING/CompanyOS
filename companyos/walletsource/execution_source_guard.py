class ExecutionSourceGuard:
    def validate(self, payload, identity):
        payload = payload or {}
        if not identity or not identity.get("success"):
            return {"allowed":False,"status":"wallet_identity_unavailable"}
        expected = identity.get("public_address")
        actual = payload.get("source")
        if not actual:
            return {"allowed":False,"status":"source_missing","expected_source":expected}
        if actual != expected:
            return {"allowed":False,"status":"source_key_mismatch_prevented","expected_source":expected,"actual_source":actual}
        return {"allowed":True,"status":"execution_source_verified","source":actual}
