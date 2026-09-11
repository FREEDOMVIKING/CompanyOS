from companyos_phase777_792 import CEOMultiProviderBridge
from .research_execution_context import ResearchExecutionContext
from .provider_result_bridge import ProviderResultBridge

class MultiProviderRuntimeAdapter:
    """795: call the multi-provider research executor from a live CEO mission."""

    DEFAULT_PROVIDERS = [
        {"name":"github","availability":0.8,"recent_failures":0},
        {"name":"public_web","availability":0.95,"recent_failures":0},
        {"name":"hacker_news","availability":0.9,"recent_failures":0},
        {"name":"local_cache","availability":1.0,"recent_failures":0},
    ]

    def __init__(self, root):
        self.root = root
        self.bridge = CEOMultiProviderBridge(root)

    def execute(self, mission, execution_result=None):
        ctx = ResearchExecutionContext().build(mission)
        provider_context = ProviderResultBridge().build(mission, execution_result)

        return self.bridge.execute(
            mission=mission,
            query=ctx["query"],
            query_type=ctx["query_type"],
            preferred_provider=ctx["preferred_provider"],
            providers=self.DEFAULT_PROVIDERS,
            context=provider_context,
        )
