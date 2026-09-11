class ControlEvidenceCollector:
    def collect(self, controls, evidence):
        evidence=evidence or {}
        return [{
            "control":c,
            "evidence":evidence.get(c,[]),
            "evidence_present":bool(evidence.get(c))
        } for c in (controls or [])]
