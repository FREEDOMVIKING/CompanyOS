from .evidence_gate import EvidenceGate
from .validation_metrics_store import ValidationMetricsStore
from .operations_metrics_store import OperationsMetricsStore

class GateResolver:
    """486: resolve CEO waiting gates from persistent evidence stores."""

    def __init__(self, root):
        self.validation = ValidationMetricsStore(root)
        self.operations = OperationsMetricsStore(root)
        self.gate = EvidenceGate()

    def resolve_validation(self, key):
        metrics = self.validation.get(key)
        return {"metrics":metrics, "gate":self.gate.evaluate("validation", metrics)}

    def resolve_operations(self, venture_id):
        metrics = self.operations.get(venture_id)
        return {"metrics":metrics, "gate":self.gate.evaluate("operations", metrics)}
