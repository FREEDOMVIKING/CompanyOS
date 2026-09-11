class LocalSignatureCheck:
    def verify_structure(self, signer_result):
        signer_result = signer_result or {}
        signature = (
            signer_result.get("signature")
            or signer_result.get("signed_message")
            or signer_result.get("signed_transaction")
            or signer_result.get("signed_transaction_hex")
        )
        public_key = signer_result.get("public_key") or signer_result.get("address")

        return {
            "passed": bool(signature),
            "signature_present": bool(signature),
            "public_key_present": bool(public_key),
            "cryptographic_verification_performed": False,
            "note":"Structural validation only unless the configured signer returns verifiable public-key/signature material."
        }
