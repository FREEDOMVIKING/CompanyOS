from companyos_phase745_760 import ResearchQualityRuntime, CEOResearchSummary
class EvidenceQualityGate:
    """764: gate lifecycle progress on evidence quality, not raw record count."""
    def evaluate(self,providers,evidence,claims=None):
        packet=ResearchQualityRuntime().run(providers,evidence,claims or [])
        summary=CEOResearchSummary().build(packet)
        return {
            "passed": summary["decision"]=="advance_to_validation",
            "packet":packet,
            "summary":summary,
        }
