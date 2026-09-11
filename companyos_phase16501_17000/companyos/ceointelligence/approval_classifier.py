class ApprovalClassifier:
    GATED_KINDS = {
        "bank_transfer",
        "contract_signature",
        "production_deploy",
        "public_launch",
        "send_external_message",
        "large_purchase",
        "delete_production_data",
    }

    def classify(self, task):
        kind = str(task.get("kind", "")).strip().lower()
        explicitly = bool(task.get("requires_approval", False))
        gated = explicitly or kind in self.GATED_KINDS
        return {
            "requires_approval": gated,
            "reason": "explicit_or_consequential_action" if gated else "within_delegated_internal_authority"
        }
