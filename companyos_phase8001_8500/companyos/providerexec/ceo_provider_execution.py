from .adapter_registry import AdapterRegistry
from .http_adapter import HTTPProviderAdapter
from .command_adapter import CommandProviderAdapter
from .smtp_adapter import SMTPProviderAdapter
from .research_adapter import ResearchProviderAdapter
from .deployment_adapter import DeploymentProviderAdapter
from .finance_read_adapter import FinanceReadAdapter
from .provider_executor import ProviderExecutor
from .receipt_verifier import ProviderReceiptVerifier
from .approval_gate import ProviderApprovalGate
from .provider_state import ProviderExecutionState
from .provider_audit import ProviderExecutionAudit

class CEOProviderExecutionController:
    def __init__(self, root):
        self.root=root
        self.registry=AdapterRegistry()
        for a in [HTTPProviderAdapter(),CommandProviderAdapter(),SMTPProviderAdapter(),
                  ResearchProviderAdapter(),DeploymentProviderAdapter(),FinanceReadAdapter()]:
            self.registry.register(a)
        self.state=ProviderExecutionState(root)
        self.audit=ProviderExecutionAudit(root)

    def run(self, requests, live=False):
        executed=[]; approval=[]
        for req in requests or []:
            gate=ProviderApprovalGate().evaluate({"kind":req.get("action"),"amount":req.get("amount",0)})
            if gate["requires_approval"]:
                approval.append({**req,"gate":gate})
                continue
            candidates=self.registry.for_capability(req.get("capability"))
            adapter=candidates[0] if candidates else None
            result=ProviderExecutor().execute(adapter,req.get("request",{}),live=live,timeout=req.get("timeout",30))
            verification=ProviderReceiptVerifier().verify(result)
            executed.append({
                "request":req,
                "adapter":adapter.name if adapter else None,
                "result":result,
                "verification":verification
            })

        result={
            "success":True,
            "status":"real_provider_execution_adapter_cycle_complete",
            "live":bool(live),
            "adapter_inventory":self.registry.inventory(),
            "executed":executed,
            "approval_queue":approval
        }
        self.state.save(result)
        self.audit.append("provider_execution_cycle",result)
        return result
