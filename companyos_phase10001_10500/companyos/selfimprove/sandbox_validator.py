class SandboxValidator:
    def validate(self, proposal, tests):
        passed=all(bool(t.get("passed",False)) for t in tests or [])
        return {
            "proposal":proposal,
            "tests":tests or [],
            "passed":passed,
            "safe_for_canary":passed and bool(proposal.get("reversible"))
        }
