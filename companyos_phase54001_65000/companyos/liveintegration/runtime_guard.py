from companyos.moneyops import FinancialKillSwitch
from companyos.controlledexec import PostExecutionLock
from .live_policy import LiveExecutionPolicy

class LiveRuntimeGuard:
    def __init__(self, root):
        self.root=root
        self.kill=FinancialKillSwitch(root)
        self.postlock=PostExecutionLock(root)
        self.policy=LiveExecutionPolicy()

    def check(self):
        if self.kill.engaged():
            return {"allowed":False,"status":"financial_kill_switch_engaged"}
        lock=self.postlock.status()
        if lock.get("locked"):
            return {"allowed":False,"status":"post_execution_lock_active","lock":lock}
        if not self.policy.enabled:
            return {"allowed":False,"status":"live_execution_not_enabled"}
        return {"allowed":True,"status":"live_runtime_guard_passed","policy":self.policy.snapshot()}
