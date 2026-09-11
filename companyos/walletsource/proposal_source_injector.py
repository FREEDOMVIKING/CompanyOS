class ProposalSourceInjector:
    def inject(self, proposal, identity):
        proposal = dict(proposal or {})
        if not identity or not identity.get("success"):
            return {"success":False,"status":"wallet_identity_unavailable","proposal":proposal}
        verified = identity.get("public_address")
        existing = proposal.get("source")
        if existing and existing != verified:
            return {"success":False,"status":"proposal_source_mismatch","proposal":proposal,"verified_source":verified}
        proposal["source"] = verified
        proposal["source_verified"] = True
        proposal["source_origin"] = "secure_signer_identity"
        return {"success":True,"status":"verified_source_injected","proposal":proposal}
