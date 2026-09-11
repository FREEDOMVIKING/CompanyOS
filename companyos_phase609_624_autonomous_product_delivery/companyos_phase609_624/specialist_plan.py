class SpecialistPlan:
    """612: delivery-focused specialist assignments."""

    MAP = {
        "D1":"software_architect",
        "D2":"builder",
        "D3":"growth_analyst",
        "D4":"qa_reviewer",
        "D5":"qa_reviewer",
        "D6":"release_manager",
    }

    def assign(self, tasks):
        return [{**t, "assigned_role": self.MAP.get(t.get("id"), "builder")} for t in tasks]
