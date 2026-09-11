class ReleaseCandidateGate:
    """985-988: block release unless build, tests, safety, and rollback are ready."""
    def evaluate(self, build_loop, safety_checks=None, rollback_ready=True):
        safety_checks=list(safety_checks or [])
        safety_ok=all(bool(x.get("passed",False)) for x in safety_checks) if safety_checks else True
        passed=(
            bool(build_loop.get("build_success"))
            and bool(build_loop.get("tests_passed"))
            and safety_ok
            and bool(rollback_ready)
        )
        return {"passed":passed,"status":"release_candidate_ready" if passed else "release_candidate_blocked"}
