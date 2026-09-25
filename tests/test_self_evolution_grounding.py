import tempfile
import unittest
from pathlib import Path

from companyos.runtime.self_evolution_engine import (
    _candidate_quality_errors,
)

from companyos.runtime.self_evolution_hypothesis import (
    grounding_errors,
)


BASELINE = '''import json
rows=[]
if LEDGER.exists():
    for line in LEDGER.read_text().splitlines():
        rows.append(json.loads(line))
print(json.dumps({"rows": rows}))
'''


BAD_CANDIDATE = '''import json
if LEDGER.exists():
    print("Ledger has already been processed.")
else:
    rows=[]
    for line in LEDGER.read_text().splitlines():
        rows.append(json.loads(line))
    print(json.dumps({"rows": rows}))
'''


class GroundingTests(unittest.TestCase):

    def test_placeholder_location_rejected(self):
        plan = {
            "problem":
                "Duplicate Work Prevention",
            "location":
                "existing function or method",
            "evidence":
                "if LEDGER.exists():",
            "behavior_change":
                "avoid duplicate processing",
            "acceptance":
                "ledger only processed once",
        }

        errors = grounding_errors(
            plan,
            BASELINE,
        )

        self.assertTrue(
            any(
                x.startswith(
                    "ungrounded_location:"
                )
                for x in errors
            ),
            errors,
        )

    def test_unsupported_duplicate_claim_rejected(self):
        plan = {
            "problem":
                "Duplicate processing",
            "location":
                "<module>",
            "evidence":
                "if LEDGER.exists():",
            "behavior_change":
                "deduplicate already processed work",
            "acceptance":
                "no duplicate work",
        }

        errors = grounding_errors(
            plan,
            BASELINE,
        )

        self.assertIn(
            "unsupported_target_concept:duplicate",
            errors,
        )

    def test_json_output_contract_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            errors = _candidate_quality_errors(
                Path(td),
                "scripts/status.py",
                BAD_CANDIDATE,
                baseline=BASELINE,
                planned_paths={
                    "scripts/status.py"
                },
                is_new=False,
            )

        self.assertTrue(
            any(
                x.startswith(
                    "public_output_contract_changed:"
                )
                for x in errors
            ),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
