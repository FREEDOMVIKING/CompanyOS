from companyos_phase857_872 import EvidenceMerger
from companyos_phase841_856 import CEOValidationRuntimeBridge
class ValidationFeedbackBridge:
    """927: merge adaptive evidence and immediately rerun validation."""
    def __init__(self,root): self.validation=CEOValidationRuntimeBridge(root)
    def apply(self, mission, evidence):
        m=dict(mission or {})
        ctx=dict(m.get("context") or {})
        packet=dict(ctx.get("research_packet") or {})
        packet["evidence"]=EvidenceMerger().merge(packet.get("evidence",[]),evidence or [])
        ctx["research_packet"]=packet
        m["context"]=ctx
        return {"mission":m,"validation":self.validation.run(m)}
