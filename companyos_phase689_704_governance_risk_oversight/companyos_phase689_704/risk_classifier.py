class RiskClassifier:
    """690: low/medium/high/irreversible action risk."""

    HIGH = {
        "spend_money","transfer_funds","sign_contract","rotate_credentials",
        "grant_privileged_access","deploy_production","delete_production_data"
    }
    IRREVERSIBLE = {"create_legal_entity","delete_production_data","sign_contract"}

    def classify(self, action):
        typ = action.get("action_type")
        if typ in self.IRREVERSIBLE:
            return "irreversible"
        if typ in self.HIGH:
            return "high"
        if action.get("external"):
            return "medium"
        return "low"
