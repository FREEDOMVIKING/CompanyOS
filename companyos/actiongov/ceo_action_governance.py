from .policy_engine import ActionPolicyEngine
from .approval_queue import PersistentApprovalQueue
from .risk_scoring import ActionRiskScorer
from .budget_enforcer import BudgetEnforcer
from .rate_limiter import ActionRateLimiter
from .dual_control import DualControlPolicy
from .dry_run_engine import DryRunEngine
from .rollback_executor import RollbackExecutor
from .action_state import ActionGovernanceState
from .action_audit import ActionGovernanceAudit

class CEOActionGovernanceController:
    def __init__(self,root):
        self.queue=PersistentApprovalQueue(root)
        self.state=ActionGovernanceState(root)
        self.audit=ActionGovernanceAudit(root)

    def run(self, actions=None, available_budget=0, recent_action_count=0):
        autonomous=[]; queued=[]
        for a in actions or []:
            policy=ActionPolicyEngine().evaluate(a)
            risk=ActionRiskScorer().score(a)
            budget=BudgetEnforcer().evaluate(a,available_budget)
            rate=ActionRateLimiter().evaluate(recent_action_count)
            dry=DryRunEngine().simulate(a)
            rollback=RollbackExecutor().plan(a)
            dual=DualControlPolicy().evaluate(a,a.get("approvals",[]))

            record={
                "action":a,
                "policy":policy,
                "risk":risk,
                "budget":budget,
                "rate_limit":rate,
                "dry_run":dry,
                "rollback":rollback,
                "dual_control":dual
            }

            needs=policy["requires_approval"] or not budget["allowed"] or not rate["allowed"] or (risk["risk_level"]=="high" and not dual["satisfied"])
            if needs:
                queued.append(self.queue.submit(record))
            else:
                autonomous.append(record)

        result={
            "success":True,
            "status":"autonomous_external_action_governance_cycle_complete",
            "autonomous_actions":autonomous,
            "queued_for_approval":queued,
            "pending_approval_count":len(self.queue.pending())
        }
        self.state.save(result)
        self.audit.append("action_governance_cycle",result)
        return result
