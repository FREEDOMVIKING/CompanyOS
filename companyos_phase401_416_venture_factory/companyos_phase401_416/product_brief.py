class ProductBrief:
    """402: convert a validated thesis into a concise product brief."""

    def build(self, thesis):
        return {
            "product_name": thesis.get("name"),
            "target_customer": thesis.get("customer"),
            "problem": thesis.get("core_problem"),
            "business_model": thesis.get("business_model"),
            "primary_outcome": f"Solve {thesis.get('core_problem')} for {thesis.get('customer')}",
            "stage": "mvp",
        }
