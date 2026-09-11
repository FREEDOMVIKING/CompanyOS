from .cycle_state import CycleStateStore
from .governor import AutonomyGovernor

class AutonomousCompanyOperatingLoop:
    STAGES=["discover","research","select","plan","budget","build","test",
            "launch_review","operate","customers","revenue","accounting",
            "evaluate","portfolio_decision","learn"]

    def __init__(self,root):
        self.root=root
        self.store=CycleStateStore(root)
        self.governor=AutonomyGovernor()

    def run_cycle(self, context=None):
        context=context or {}
        state=self.store.load()
        cycle=int(state.get("cycle",0))+1
        results=[]
        for stage in self.STAGES:
            action={
                "stage":stage,
                "external":stage in ("launch_review","operate","customers"),
                "irreversible":False,
                "moves_money":stage=="budget",
                "within_policy":bool(context.get("treasury_policy_satisfied",False)),
                "requires_external_approval":stage=="launch_review",
            }
            governance=self.governor.classify(action)
            results.append({"stage":stage,"governance":governance,"completed":governance["decision"]=="autonomous_allowed"})
        blocked=[x for x in results if x["governance"]["decision"]=="blocked"]
        approvals=[x for x in results if x["governance"]["decision"]=="approval_required"]
        summary={
            "cycle":cycle,
            "success":not bool(blocked),
            "stages":results,
            "blocked_count":len(blocked),
            "approval_required_count":len(approvals),
            "next_action":"continue_autonomous_cycle" if not blocked and not approvals else "resolve_gates_then_continue"
        }
        history=(state.get("history") or [])[-19:]+[summary]
        self.store.save({"cycle":cycle,"history":history,"last_status":summary["next_action"]})
        return summary
