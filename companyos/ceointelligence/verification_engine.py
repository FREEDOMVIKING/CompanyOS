class VerificationEngine:
    def verify_execution(self, job, result):
        from companyos.cycleops import CycleVerifier
        return CycleVerifier().verify_execution(job, result)

    def summarize_cycle(self, results):
        from companyos.cycleops import CycleVerifier
        return CycleVerifier().summarize_cycle(results)
