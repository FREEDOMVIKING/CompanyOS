from .failure_classifier import FailureClassifier
from .generic_specialist import GenericSpecialist

class RecoveryRouter:
    def __init__(self, root):
        self.root = root

    def recover(self, job, department, result):
        cls = FailureClassifier().classify(job, result)
        if not cls["recoverable"]:
            return {"recovered":False,"classification":cls,"result":result}
        recovered = GenericSpecialist(self.root).execute(job, department)
        return {
            "recovered": bool(recovered.get("success")),
            "classification": cls,
            "result": recovered
        }
