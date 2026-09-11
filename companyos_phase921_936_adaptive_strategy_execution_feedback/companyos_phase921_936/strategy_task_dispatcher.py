from companyos_phase777_792 import EvidenceCollector
class StrategyTaskDispatcher:
    """922: execute an adaptive task through its changed provider mix."""
    def dispatch(self, task, provider_results):
        chain=list(task.get("provider_chain") or ["public_web"])
        batches=[]
        for provider in chain:
            result=EvidenceCollector().collect(
                provider,
                (task.get("task") or {}).get("query",""),
                {"provider_results":provider_results},
            )
            batches.append(result)
            if result.get("success") and result.get("items"):
                break
        return {"task":task,"batches":batches}
