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

from companyos.runtime.self_evolution_hypothesis import (
    novelty_errors,
)


class NoveltyTests(unittest.TestCase):

    def test_existing_duplicate_prevention_rejected(self):
        source = """
seen=set(st.get("seen_sha256", []))
for item in discover():
    if item["sha256"] in seen:
        continue
    process(item)
    seen.add(item["sha256"])
"""

        plan = {
            "problem":
                "Duplicate work can be processed twice",
            "location":
                "<module>",
            "evidence":
                'seen=set(st.get("seen_sha256", []))',
            "behavior_change":
                "Prevent duplicate processing using SHA256 identity",
            "acceptance":
                "Each item is processed only once",
        }

        errors = novelty_errors(
            plan,
            source,
        )

        self.assertIn(
            "capability_already_present:"
            "duplicate_prevention",
            errors,
        )

    def test_missing_duplicate_prevention_allowed(self):
        source = """
for item in discover():
    process(item)
"""

        plan = {
            "problem":
                "Duplicate work can be processed twice",
            "location":
                "<module>",
            "evidence":
                "for item in discover():",
            "behavior_change":
                "Prevent duplicate processing",
            "acceptance":
                "Each item is processed only once",
        }

        errors = novelty_errors(
            plan,
            source,
        )

        self.assertNotIn(
            "capability_already_present:"
            "duplicate_prevention",
            errors,
        )
