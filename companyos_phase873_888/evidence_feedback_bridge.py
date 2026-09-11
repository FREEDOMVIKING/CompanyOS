from companyos_phase857_872 import EvidenceMerger
class EvidenceFeedbackBridge:
    """877: merge new evidence into original research packet."""
    def apply(self, validation_mission, new_evidence):
        m=dict(validation_mission or {})
        ctx=dict(m.get("context") or {})
        packet=dict(ctx.get("research_packet") or {})
        packet["evidence"]=EvidenceMerger().merge(packet.get("evidence",[]),new_evidence)
        ctx["research_packet"]=packet
        m["context"]=ctx
        return m
