from .retry_classifier import RetryClassifier
from .backoff_policy import BackoffPolicy
from .fallback_provider import FallbackProvider
from .mission_rescheduler import MissionRescheduler
from .provider_cooldown import ProviderCooldown
class ResilientExecutor:
    def __init__(self,root): self.cooldowns=ProviderCooldown(root)
    def handle(self,mission,result,current_provider="github"):
        c=RetryClassifier().classify(result)
        if not c["retryable"]:
            return {"handled":False,"hard_failure":c["hard_failure"],"result":result}
        delay=BackoffPolicy().delay_seconds(int((mission or {}).get("attempts",0)))
        self.cooldowns.set(current_provider,delay,c["reason"])
        unavailable=[p for p in FallbackProvider.ORDER if self.cooldowns.active(p)]
        fallback=FallbackProvider().choose(current_provider,unavailable)
        deferred=MissionRescheduler().reschedule(mission,delay,c["reason"],fallback)
        return {"handled":True,"hard_failure":False,"status":"provider_temporarily_unavailable","mission":deferred,"fallback_provider":fallback,"delay_seconds":delay,"classification":c}
