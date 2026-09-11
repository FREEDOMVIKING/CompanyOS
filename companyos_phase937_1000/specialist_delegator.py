class SpecialistDelegator:
    """969-972: delegate build work to specialist agents."""
    def assign(self, scope):
        return [
            {"role":"product_architect","task":"translate MVP scope into technical design"},
            {"role":"builder","task":"implement core product"},
            {"role":"qa_engineer","task":"test functionality and regressions"},
            {"role":"security_reviewer","task":"check secrets, permissions, and risky actions"},
            {"role":"release_manager","task":"prepare release candidate and rollback plan"},
        ]
