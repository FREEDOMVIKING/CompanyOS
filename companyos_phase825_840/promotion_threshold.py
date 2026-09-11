from companyos_phase745_760 import EvidenceCompleteness, EvidenceConfidence, SourceDiversifier

class PromotionThreshold:
    """835: promote only when quality and diversity thresholds are met."""

    def evaluate(self, evidence, min_confidence=0.7, min_classes=2):
        completeness = EvidenceCompleteness().evaluate(evidence or [])
        confidence = EvidenceConfidence().score(evidence or [])
        diversity = SourceDiversifier().evaluate(evidence or [])

        passed = (
            completeness.get("complete")
            and confidence >= float(min_confidence)
            and int(diversity.get("class_count",0)) >= int(min_classes)
        )

        return {
            "passed": passed,
            "confidence": confidence,
            "completeness": completeness,
            "diversity": diversity,
        }
