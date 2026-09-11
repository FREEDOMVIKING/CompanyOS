import os

class ProviderRouter:
    """
    Provider abstraction for future LLM integrations.
    V6 stays operational without any provider configured.
    """
    def __init__(self):
        self.mode=os.environ.get("COMPANYOS_AI_MODE","local").strip().lower()
        self.provider=os.environ.get("COMPANYOS_AI_PROVIDER","none").strip().lower()
        self.model=os.environ.get("COMPANYOS_AI_MODEL","").strip()

    def status(self):
        configured=self.provider not in ("","none")
        return {
            "mode":self.mode,
            "provider":self.provider,
            "model":self.model or None,
            "configured":configured,
            "local_fallback_enabled":True
        }

    def executive_summary(self, company):
        if self.provider in ("","none"):
            return {
                "source":"local_deterministic_planner",
                "summary":f"Prioritize validation, product readiness, acquisition readiness, and economics for {company['name']}."
            }
        return {
            "source":"provider_adapter_not_connected",
            "summary":f"Provider '{self.provider}' is configured by name, but no external adapter is installed in V6."
        }
