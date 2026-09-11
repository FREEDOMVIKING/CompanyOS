from companyos_phase745_760 import SourceDiversifier
class DiversityGate:
    """786: require multiple source classes when possible."""
    def evaluate(self, evidence, minimum_classes=2):
        result=SourceDiversifier().evaluate(evidence)
        return {
            **result,
            "passed":result.get("class_count",0) >= minimum_classes,
            "minimum_classes":minimum_classes,
        }
