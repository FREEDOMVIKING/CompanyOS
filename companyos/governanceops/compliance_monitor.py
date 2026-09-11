class ContinuousComplianceMonitor:
    def evaluate(self, matrix, evidence):
        missing_requirements=[x["requirement"] for x in matrix or [] if not x.get("compliant")]
        missing_evidence=[x["control"] for x in evidence or [] if not x.get("evidence_present")]
        return {
            "compliant":not missing_requirements and not missing_evidence,
            "missing_requirements":missing_requirements,
            "missing_evidence":missing_evidence
        }
