class AgentPermission:
    """696: specialist-agent permission boundaries."""

    ROLE_CAPABILITIES = {
        "product_manager":{"plan","draft","prioritize"},
        "software_architect":{"plan","analyze","refactor"},
        "builder":{"write_internal_file","run_internal_test","refactor"},
        "qa_reviewer":{"run_internal_test","analyze","generate_report"},
        "growth_analyst":{"research","analyze","draft"},
        "release_manager":{"plan","simulate","generate_report"},
    }

    def check(self, role, action_type):
        allowed = self.ROLE_CAPABILITIES.get(role,set())
        return {"allowed": action_type in allowed, "role": role, "action_type": action_type}
