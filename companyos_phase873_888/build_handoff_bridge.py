from companyos_phase841_856 import BuildPromotionBridge, ValidationMissionAdapter
class BuildHandoffBridge:
    """884: produce build mission on converged GO."""
    def build(self,mission,validation):
        adapted=ValidationMissionAdapter().adapt(mission)
        return BuildPromotionBridge().build(adapted,validation)
