class OrganizationalFailureRecovery:
    def evaluate(self, failures):
        actions=[]
        for f in failures or []:
            kind=f.get("kind")
            if kind=="agent_failure":
                action="reassign_and_retry"
            elif kind=="department_overload":
                action="spawn_temporary_specialist"
            elif kind=="budget_overrun":
                action="freeze_nonessential_spend"
            elif kind=="venture_health":
                action="enter_recovery_mode"
            else:
                action="diagnose"
            actions.append({**f,"recovery_action":action})
        return actions
