from companyos_phase777_792 import EvidenceCollector
class RevalidationTaskExecutor:
    """873: execute targeted revalidation tasks through provider chains."""
    def execute(self, task, provider_results=None):
        provider_results = provider_results or {}
        chain = list(task.get("provider_chain") or ["public_web"])
        batches = []
        for provider in chain:
            result = EvidenceCollector().collect(
                provider,
                (task.get("task") or {}).get("query",""),
                {"provider_results":provider_results},
            )
            batches.append(result)
            if result.get("success") and result.get("items"):
                break
        return {"task":task,"batches":batches}
