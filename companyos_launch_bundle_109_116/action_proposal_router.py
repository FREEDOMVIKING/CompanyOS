from __future__ import annotations
from companyos.runtime.approval_queue import ApprovalQueue

class ActionProposalRouter:
    """
    Converts sensitive/intended external actions into approval items.
    Does not execute the action itself.
    """
    def __init__(self, approvals=None):
        self.approvals = approvals or ApprovalQueue()

    def propose(self, *, title, action_type, reason, payload=None):
        return self.approvals.add(title, action_type, reason, payload or {})
