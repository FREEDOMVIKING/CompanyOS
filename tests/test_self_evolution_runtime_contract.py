import tempfile
import unittest
from pathlib import Path

from companyos.runtime.self_evolution_engine import (
    _candidate_quality_errors,
)


BASELINE = '''
class Recovery:
    def plan(self, rows):
        return list(rows or [])
'''


BAD = '''
class Recovery:
    def plan(self, rows):
        try:
            return list(rows or [])
        except Exception as exc:
            self.log_failure(exc)
            return []

    def log_failure(self, exc):
        self.root.log.error(str(exc))
'''


GOOD = '''
class Recovery:
    def __init__(self):
        self.failure_count = 0

    def plan(self, rows):
        try:
            return list(rows or [])
        except Exception:
            self.failure_count += 1
            return []
'''


class RuntimeContractTests(
    unittest.TestCase
):

    def test_invented_dependency_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            errors=_candidate_quality_errors(
                Path(td),
                "companyos/example.py",
                BAD,
                baseline=BASELINE,
                planned_paths={
                    "companyos/example.py"
                },
                is_new=False,
            )

        self.assertIn(
            "introduced_unbound_self_attribute:root",
            errors,
        )

    def test_initialized_attribute_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            errors=_candidate_quality_errors(
                Path(td),
                "companyos/example.py",
                GOOD,
                baseline=BASELINE,
                planned_paths={
                    "companyos/example.py"
                },
                is_new=False,
            )

        self.assertNotIn(
            "introduced_unbound_self_attribute:failure_count",
            errors,
        )


if __name__=="__main__":
    unittest.main()
