class ImplementationPlan:
    """611: dependency-aware delivery plan."""

    def build(self, spec):
        return [
            {"id":"D1","task":"finalize interfaces and data contracts","depends_on":[]},
            {"id":"D2","task":"implement core value workflow","depends_on":["D1"]},
            {"id":"D3","task":"implement onboarding and telemetry","depends_on":["D2"]},
            {"id":"D4","task":"add targeted and regression tests","depends_on":["D2","D3"]},
            {"id":"D5","task":"run QA and repair loop","depends_on":["D4"]},
            {"id":"D6","task":"prepare release candidate","depends_on":["D5"]},
        ]
