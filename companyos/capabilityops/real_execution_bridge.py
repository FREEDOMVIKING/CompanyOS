import os
from .http_provider import HTTPJSONProvider
from .research_router import ResearchRouter
from .execution_receipt import ExecutionReceiptStore
from .memory_bridge import MemoryBridge
from .capability_policy import CapabilityPolicy

class RealExecutionBridge:
    DEPARTMENT_CAPABILITY={
        "research":"research",
        "product":"reasoning",
        "growth":"reasoning",
        "finance":"finance_read",
        "customer_success":"reasoning",
        "operations":"reasoning"
    }

    ENV_URL={
        "reasoning":"COMPANYOS_REASONING_URL",
        "research":"COMPANYOS_RESEARCH_URL",
        "communications":"COMPANYOS_COMMUNICATIONS_URL",
        "deployment":"COMPANYOS_DEPLOY_URL",
        "finance_read":"COMPANYOS_FINANCE_READ_URL"
    }

    ENV_KEY={
        "reasoning":"COMPANYOS_REASONING_API_KEY",
        "research":"COMPANYOS_RESEARCH_API_KEY",
        "communications":"COMPANYOS_COMMUNICATIONS_API_KEY",
        "deployment":"COMPANYOS_DEPLOY_API_KEY",
        "finance_read":"COMPANYOS_FINANCE_READ_API_KEY"
    }

    def __init__(self, root):
        self.root=root
        self.receipts=ExecutionReceiptStore(root)
        self.memory=MemoryBridge(root)

    def execute(self, job, department):
        payload=job.get("payload",{})
        action_kind=payload.get("action_kind") or job.get("kind","internal_analysis")
        approval=bool(payload.get("approval",False))
        policy=CapabilityPolicy().evaluate(action_kind,approval=approval)
        if not policy["allowed"]:
            result={"success":False,"blocked":True,"reason":"approval_required","action_kind":action_kind}
            self.receipts.record(job,"policy",result)
            return result

        capability=self.DEPARTMENT_CAPABILITY.get(department,"reasoning")
        url=os.getenv(self.ENV_URL[capability],"")
        key_env=self.ENV_KEY[capability]

        if not url:
            result={
                "success":True,
                "mode":"internal_fallback",
                "capability":capability,
                "job_id":job.get("job_id"),
                "department":department,
                "result":"capability_not_configured_internal_only"
            }
            self.memory.remember("fallback_execution",result)
            self.receipts.record(job,capability,result)
            return result

        request_payload={
            "job_id":job.get("job_id"),
            "department":department,
            "kind":job.get("kind"),
            "payload":payload,
            "memory":self.memory.recent(10)
        }
        if capability=="research":
            request_payload["research_request"]=ResearchRouter().build_request(job)

        result=HTTPJSONProvider().call(url,request_payload,api_key_env=key_env,timeout=60)
        self.memory.remember("capability_execution",{
            "job_id":job.get("job_id"),
            "capability":capability,
            "success":result.get("success")
        })
        receipt=self.receipts.record(job,capability,result)
        return {**result,"capability":capability,"receipt_digest":receipt["digest"]}
