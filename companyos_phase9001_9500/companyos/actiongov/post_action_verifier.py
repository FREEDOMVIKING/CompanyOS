class PostActionVerifier:
    def verify(self, expected, actual):
        checks={}
        for k,v in (expected or {}).items():
            checks[k]=(actual or {}).get(k)==v
        return {"verified":all(checks.values()) if checks else True,"checks":checks}
