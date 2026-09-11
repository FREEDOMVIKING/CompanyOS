from companyos_phase745_760 import ResearchQualityRuntime, CEOResearchSummary
class ResearchPacketAssembler:
    """790: assemble merged evidence into CEO-quality research packet."""
    def assemble(self, providers, evidence, claims=None):
        packet=ResearchQualityRuntime().run(providers,evidence,claims or [])
        packet["summary"]=CEOResearchSummary().build(packet)
        return packet
