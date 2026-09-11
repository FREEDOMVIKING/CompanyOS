class ProductSpec:
    """610: convert venture context into explicit product acceptance criteria."""

    def build(self, packet):
        brief = packet.get("brief") or {}
        scope = packet.get("mvp_scope") or {}
        return {
            "product_name": brief.get("product_name"),
            "target_customer": brief.get("target_customer"),
            "problem": brief.get("problem"),
            "stage": "mvp_delivery",
            "must_have": list(scope.get("must_have", [])),
            "defer": list(scope.get("defer", [])),
            "acceptance_criteria": [
                "core value workflow works end-to-end",
                "targeted tests pass",
                "regression tests pass",
                "telemetry emits expected events",
                "rollback path is documented",
            ],
        }
