class ProviderReceiptVerifier:
    def verify(self, result):
        return {
            "verified":bool((result or {}).get("success")),
            "adapter":(result or {}).get("adapter"),
            "simulated":bool((result or {}).get("simulated",False))
        }
