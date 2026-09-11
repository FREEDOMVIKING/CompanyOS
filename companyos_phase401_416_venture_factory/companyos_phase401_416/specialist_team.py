class SpecialistTeam:
    """405: define specialist-agent roles for an MVP build."""

    def assign(self, brief):
        return [
            {"role":"product_manager","owns":["requirements","scope","acceptance criteria"]},
            {"role":"software_architect","owns":["architecture","interfaces","technical risk"]},
            {"role":"builder","owns":["implementation","unit tests","documentation"]},
            {"role":"qa_reviewer","owns":["verification","regression","quality gates"]},
            {"role":"growth_analyst","owns":["activation instrumentation","funnel metrics","experiment hooks"]},
        ]
