from companyos_phase433_448 import CEOPortfolioRouter

class PortfolioStage:
    """475: allocate attention across ventures."""

    def __init__(self):
        self.router = CEOPortfolioRouter()

    def run(self, context=None):
        context = context or {}
        ventures = context.get("ventures") or []

        if not ventures:
            return {
                "success":True,
                "status":"portfolio_empty",
                "stage":"portfolio",
                "data":{"decision":"discover_more"},
            }

        plan = self.router.route(ventures, max_active=2)
        return {
            "success":True,
            "status":"portfolio_routing_ready",
            "stage":"portfolio",
            "data":{"portfolio_plan":plan,"decision":"hold_for_more_evidence"},
        }
