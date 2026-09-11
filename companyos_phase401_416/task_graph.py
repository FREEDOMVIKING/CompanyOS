class TaskGraph:
    """406: dependency-aware MVP task graph."""

    def create(self):
        return [
            {"id":"T1","task":"finalize product brief","depends_on":[]},
            {"id":"T2","task":"freeze MVP scope","depends_on":["T1"]},
            {"id":"T3","task":"define architecture and interfaces","depends_on":["T2"]},
            {"id":"T4","task":"implement core value loop","depends_on":["T3"]},
            {"id":"T5","task":"add onboarding and telemetry","depends_on":["T4"]},
            {"id":"T6","task":"run quality gates","depends_on":["T4","T5"]},
            {"id":"T7","task":"prepare release candidate","depends_on":["T6"]},
        ]
