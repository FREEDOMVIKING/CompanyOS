class ExternalActionPolicy:
    """694: policy for externally visible actions."""

    SENSITIVE = {
        "publish_publicly","contact_customer_externally","deploy_production",
        "change_billing","sign_contract","create_legal_entity"
    }

    def evaluate(self, action):
        typ = action.get("action_type")
        return {
            "external": bool(action.get("external")) or typ in self.SENSITIVE,
            "requires_review": typ in self.SENSITIVE,
            "reversible_preferred": True,
        }
