class PortfolioScenarioEngine:
    def model(self, ventures, shock=-.2, upside=.25):
        base=sum(float(v.get("revenue",0)) for v in ventures or [])
        return {
            "base_revenue":round(base,2),
            "downside_revenue":round(base*(1+float(shock)),2),
            "upside_revenue":round(base*(1+float(upside)),2),
            "survival_focus":"preserve_cash_and_core_ventures" if shock<-.15 else "balanced"
        }
