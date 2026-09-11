class PlanningHorizons:
    def build(self, goals):
        goals=list(goals or [])
        return {
            "daily":[g for g in goals if g.get("type") in ("execution","measurement")],
            "weekly":[g for g in goals if g.get("type") in ("research","learning","execution")],
            "monthly":[g for g in goals if g.get("type") in ("strategy","learning")],
            "quarterly":[{"objective":"portfolio review and capital reallocation","type":"strategy"}],
        }
