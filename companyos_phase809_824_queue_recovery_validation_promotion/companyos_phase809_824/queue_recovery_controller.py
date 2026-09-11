from companyos_phase481_496 import MissionQueue
from .queue_snapshot import QueueSnapshot
from .deferred_selector import DeferredSelector
from .retry_loop_guard import RetryLoopGuard
from .alternate_provider_recovery import AlternateProviderRecovery
from .promotion_gate import PromotionGate
from .validation_promoter import ValidationPromoter
from .supersession_policy import SupersessionPolicy
from .evidence_merge_bridge import EvidenceMergeBridge
from .queue_compactor import QueueCompactor
from .queue_drain_metrics import QueueDrainMetrics
from .recovery_audit import RecoveryAudit

class QueueRecoveryController:
    """822: recover, promote, compact, and persist queued missions."""

    def __init__(self, root):
        self.root = root
        self.queue = MissionQueue(root)
        self.audit = RecoveryAudit(root)

    def run_once(self, max_recoveries=3):
        missions = self.queue.load()
        before = QueueSnapshot().build(missions)

        compacted = QueueCompactor().compact(missions)
        missions = compacted["missions"]

        recovered = []
        promoted = []
        retained = []

        candidates = DeferredSelector().select(missions)[:max(1, int(max_recoveries))]
        candidate_ids = {m.get("mission_id") for m in candidates}

        for mission in missions:
            if mission.get("mission_id") not in candidate_ids:
                retained.append(mission)
                continue

            guard = RetryLoopGuard().evaluate(mission)
            if not guard["allowed"]:
                retired = dict(mission)
                retired["status"] = "retired"
                retired["retire_reason"] = "retry_limit_reached"
                recovered.append({"mission_id":mission.get("mission_id"),"status":"retired_retry_limit"})
                continue

            result = AlternateProviderRecovery(self.root).recover(mission)
            gate = PromotionGate().evaluate(result)

            if gate["promote"]:
                validation = ValidationPromoter().promote(result)
                if validation:
                    promoted.append(validation)
                recovered.append({
                    "mission_id":mission.get("mission_id"),
                    "status":"promoted",
                    "confidence":gate["confidence"],
                })
                continue

            updated = EvidenceMergeBridge().apply(mission, result)
            updated["status"] = "deferred"
            retained.append(updated)
            recovered.append({
                "mission_id":mission.get("mission_id"),
                "status":"retained_research",
                "confidence":gate["confidence"],
            })

        final = retained + promoted
        final = QueueCompactor().compact(final)["missions"]
        self.queue.save(final)

        after = QueueSnapshot().build(final)
        metrics = QueueDrainMetrics().compare(before, after)

        result = {
            "success": True,
            "status": "queue_recovery_cycle_complete",
            "before": before,
            "after": after,
            "metrics": metrics,
            "recovered": recovered,
            "promoted_count": len(promoted),
            "retired_count": len(compacted["retired"]),
        }
        self.audit.append(result)
        return result
