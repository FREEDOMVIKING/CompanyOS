from companyos_phase737_744 import ProviderCooldown
from companyos_phase745_760 import ProviderSelector
class ProviderHealthBridge:
    """763: combine cooldown state with provider quality ranking."""
    def __init__(self,root):
        self.cooldowns=ProviderCooldown(root)
    def select(self, providers):
        enriched=[]
        for p in providers or []:
            item=dict(p)
            item["cooldown_active"]=self.cooldowns.active(item.get("name","unknown"))
            enriched.append(item)
        return ProviderSelector().choose(enriched)
