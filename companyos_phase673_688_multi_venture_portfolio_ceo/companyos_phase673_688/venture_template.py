class VentureTemplate:
    """679: standard company/venture creation template."""

    def create(self, name, category, thesis):
        return {
            "name":name,
            "category":category,
            "stage":"incubating",
            "thesis":thesis,
            "required_systems":[
                "product",
                "telemetry",
                "customer_feedback",
                "financial_tracking",
                "operations",
            ],
            "shared_first":True,
        }
