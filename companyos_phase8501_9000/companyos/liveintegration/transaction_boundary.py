class TransactionBoundary:
    def classify(self, action):
        kind=action.get("kind","")
        irreversible=kind in {"bank_transfer","contract_signature","legal_filing","acquisition","delete_external_resource"}
        external=bool(action.get("external",True))
        return {
            "kind":kind,
            "irreversible":irreversible,
            "external":external,
            "boundary":"approval" if irreversible or external else "autonomous"
        }
