class LandingPageSpec:
    """388: build a validation-only landing-page specification."""

    def build(self, thesis):
        return {
            "headline": thesis.get("name"),
            "audience": thesis.get("customer"),
            "problem": thesis.get("core_problem"),
            "promise": "A faster, simpler way to solve this workflow problem.",
            "cta": "Join early access",
            "collect": ["email","company","role","problem severity"],
            "purpose": "validation_only",
        }
