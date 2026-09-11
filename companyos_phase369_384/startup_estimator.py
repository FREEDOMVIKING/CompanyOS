from __future__ import annotations

class StartupEstimator:
    """378: rough build/validation effort class before capital allocation."""

    def estimate(self, theme):
        heavy = ("integration_sync","compliance_admin")
        if theme in heavy:
            return {"complexity":"medium","estimated_initial_build_weeks":[4,10],"capital_intensity":"low_to_medium"}
        return {"complexity":"low_to_medium","estimated_initial_build_weeks":[2,6],"capital_intensity":"low"}
