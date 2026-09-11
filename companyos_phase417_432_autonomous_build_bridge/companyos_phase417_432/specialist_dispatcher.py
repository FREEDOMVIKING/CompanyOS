class SpecialistDispatcher:
    """418: route work to bounded specialist roles."""

    ROLE_MAP = {
        "product_manager":["requirements","scope","acceptance criteria"],
        "software_architect":["architecture","interfaces","technical risk"],
        "builder":["implementation","unit tests","documentation"],
        "qa_reviewer":["verification","regression","quality gates"],
        "growth_analyst":["activation instrumentation","funnel metrics","experiment hooks"],
    }

    def dispatch(self, task_graph):
        jobs = []
        for task in task_graph:
            text = task.get("task","").lower()
            if "architecture" in text:
                role = "software_architect"
            elif "quality" in text or "test" in text:
                role = "qa_reviewer"
            elif "telemetry" in text or "onboarding" in text:
                role = "growth_analyst"
            elif "implement" in text or "release candidate" in text:
                role = "builder"
            else:
                role = "product_manager"
            jobs.append({**task, "assigned_role":role, "role_contract":self.ROLE_MAP[role]})
        return jobs
