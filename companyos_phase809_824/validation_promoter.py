from companyos_phase793_808 import ValidationQueueBridge

class ValidationPromoter:
    """817: turn qualified recovery result into queued validation mission."""

    def promote(self, recovery_result):
        next_mission = (recovery_result or {}).get("next_mission")
        return ValidationQueueBridge().build(next_mission)
