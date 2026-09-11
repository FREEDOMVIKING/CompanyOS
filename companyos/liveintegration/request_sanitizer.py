class RequestSanitizer:
    REDACT_KEYS={"password","secret","private_key","seed_phrase","api_key","token"}
    def sanitize(self, payload):
        def clean(v):
            if isinstance(v,dict):
                out={}
                for k,val in v.items():
                    if any(x in str(k).lower() for x in self.REDACT_KEYS):
                        out[k]="***REDACTED***"
                    else:
                        out[k]=clean(val)
                return out
            if isinstance(v,list):
                return [clean(x) for x in v]
            return v
        return clean(payload or {})
