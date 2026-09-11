class AuthorityMatrix:
    """689: define which actions are autonomous vs approval-gated."""

    AUTONOMOUS = {
        "research","analyze","plan","draft","test","simulate","refactor",
        "write_internal_file","run_internal_test","generate_report",
        "prioritize","queue_mission","update_internal_state"
    }

    APPROVAL = {
        "spend_money","transfer_funds","sign_contract","create_legal_entity",
        "delete_production_data","rotate_credentials","publish_publicly",
        "contact_customer_externally","deploy_production","change_billing",
        "grant_privileged_access"
    }

    def classify(self, action_type):
        if action_type in self.AUTONOMOUS:
            return "autonomous"
        if action_type in self.APPROVAL:
            return "approval_required"
        return "review_required"
