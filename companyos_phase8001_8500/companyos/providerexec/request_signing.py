class RequestSigningPolicy:
    def headers(self, auth_scheme, credential_ref=None):
        if auth_scheme=="bearer" and credential_ref:
            return {"Authorization":"Bearer ${%s}"%credential_ref}
        if auth_scheme=="api_key" and credential_ref:
            return {"X-API-Key":"${%s}"%credential_ref}
        return {}
