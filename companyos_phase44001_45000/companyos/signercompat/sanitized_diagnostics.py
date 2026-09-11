SENSITIVE_KEYS = {
    "private_key","seed","seed_phrase","mnemonic","secret","password",
    "api_key","token","signed_transaction","signed_transaction_hex",
    "signed_transaction_base64"
}

class SanitizedDiagnostics:
    def sanitize(self, value):
        if isinstance(value, dict):
            out = {}
            for k,v in value.items():
                if str(k).lower() in SENSITIVE_KEYS:
                    out[k] = "***REDACTED***"
                else:
                    out[k] = self.sanitize(v)
            return out
        if isinstance(value, list):
            return [self.sanitize(v) for v in value]
        return value
