class ScenarioPlanner:
    def run(self, base, upside, downside):
        return {
            "base":base,
            "upside":upside,
            "downside":downside,
            "recommended_posture":"balanced" if downside.get("survival",True) else "defensive"
        }
