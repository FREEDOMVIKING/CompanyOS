import tempfile
import unittest
from pathlib import Path

from companyos.runtime.self_evolution_engine import (
    _candidate_quality_errors,
)


OLD_ROUTER = '''class WorkerRouter:
    ROUTES={
        "research":"research",
        "build":"product"
    }

    def route(self, job):
        payload=job.get("payload",{})
        dept=payload.get("department")
        return dept or self.ROUTES.get(
            job.get("kind"),
            "operations"
        )
'''


REFACTOR_ONLY = '''class WorkerRouter:
    ROUTES = {
        "research": "research",
        "build": "product"
    }

    def route(self, job):
        payload = job.get("payload", {})
        department = payload.get("department")
        if department:
            return department
        kind = job.get("kind")
        return self.ROUTES.get(
            kind,
            "operations"
        )
'''


REAL_BEHAVIOR = '''class WorkerRouter:
    ROUTES={
        "research":"research",
        "build":"product"
    }

    def route(self, job):
        if not isinstance(job, dict):
            raise TypeError("job must be a mapping")

        payload=job.get("payload",{})

        if not isinstance(payload,dict):
            raise TypeError(
                "payload must be a mapping"
            )

        dept=payload.get("department")

        return dept or self.ROUTES.get(
            job.get("kind"),
            "operations"
        )
'''


class CapabilityGateTests(unittest.TestCase):

    def test_equivalent_router_refactor_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            errors=_candidate_quality_errors(
                Path(td),
                "companyos/workerops/worker_router.py",
                REFACTOR_ONLY,
                baseline=OLD_ROUTER,
                planned_paths={
                    "companyos/workerops/worker_router.py"
                },
                is_new=False,
            )

        self.assertTrue(
            any(
                x.startswith(
                    "low_capability_novelty:"
                )
                for x in errors
            ),
            errors,
        )

    def test_real_validation_behavior_has_capability_gain(self):
        with tempfile.TemporaryDirectory() as td:
            errors=_candidate_quality_errors(
                Path(td),
                "companyos/workerops/worker_router.py",
                REAL_BEHAVIOR,
                baseline=OLD_ROUTER,
                planned_paths={
                    "companyos/workerops/worker_router.py"
                },
                is_new=False,
            )

        self.assertFalse(
            any(
                x.startswith(
                    "low_capability_novelty:"
                )
                for x in errors
            ),
            errors,
        )


if __name__=="__main__":
    unittest.main()
