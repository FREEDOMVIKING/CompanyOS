class SecretReferenceAudit:
    SENSITIVE_KEYS={"api_key","secret","password","private_key","seed_phrase","token"}

    def inspect(self, config):
        findings=[]
        for k,v in (config or {}).items():
            lk=str(k).lower()
            if any(x in lk for x in self.SENSITIVE_KEYS):
                if isinstance(v,str) and not (v.startswith("${") or v.startswith("env:")):
                    findings.append({"key":k,"issue":"plaintext_secret_reference"})
        return {"safe":not findings,"findings":findings}
