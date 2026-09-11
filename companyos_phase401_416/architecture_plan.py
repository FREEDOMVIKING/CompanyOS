class ArchitecturePlan:
    """404: create an implementation-neutral architecture contract."""

    def build(self, brief):
        return {
            "interfaces": ["user_interface", "application_service", "data_store", "telemetry"],
            "principles": [
                "modular",
                "testable",
                "replaceable_components",
                "configuration_over_hardcoding",
                "observable_runtime",
            ],
            "security_baseline": [
                "secrets_outside_source",
                "least_privilege",
                "input_validation",
                "audit_relevant_actions",
            ],
            "product": brief.get("product_name"),
        }
