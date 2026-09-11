import json
import tempfile
import unittest
from pathlib import Path

from companyos.console.aggregator import ConsoleAggregator
from companyos.console.control import ALLOWED_ACTIONS
from companyos.console.storage import read_json

class ConsoleTests(unittest.TestCase):
    def test_allowed_controls(self):
        self.assertEqual(ALLOWED_ACTIONS, {"start", "stop", "restart", "status"})

    def test_missing_json_returns_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(read_json(Path(tmp) / "missing.json", {"ok": True}), {"ok": True})

    def test_snapshot_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "companyos_runtime" / "phase18201_18300").mkdir(parents=True)
            (home / "companyos_runtime" / "controlplane").mkdir(parents=True)
            snapshot = ConsoleAggregator(home).snapshot()
            self.assertEqual(snapshot["phase"], "18401-18500")
            self.assertIn("ventures", snapshot)
            self.assertIn("tasks", snapshot)
            self.assertIn("workers", snapshot)
            self.assertIn("finance", snapshot)

    def test_venture_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            exec_dir = home / "companyos_runtime" / "phase18201_18300"
            control_dir = home / "companyos_runtime" / "controlplane"
            exec_dir.mkdir(parents=True)
            control_dir.mkdir(parents=True)

            (exec_dir / "ventures.json").write_text(json.dumps([
                {"venture_id":"v1","name":"Venture One","stage":"build","progress":0.5}
            ]))
            (exec_dir / "latest_priority_ranking.json").write_text(json.dumps([
                {"venture_id":"v1","score":1.25}
            ]))
            (exec_dir / "latest_executive_decisions.json").write_text(json.dumps([
                {"venture_id":"v1","scale_action":"hold_and_measure","capital_proposed":125}
            ]))

            snapshot = ConsoleAggregator(home).snapshot()
            self.assertEqual(snapshot["ventures"][0]["priority_score"], 1.25)
            self.assertEqual(snapshot["ventures"][0]["capital_proposed"], 125)

    def test_finance_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            exec_dir = home / "companyos_runtime" / "phase18201_18300"
            control_dir = home / "companyos_runtime" / "controlplane"
            exec_dir.mkdir(parents=True)
            control_dir.mkdir(parents=True)

            (exec_dir / "finance_state.json").write_text(json.dumps({"available_capital":1000}))
            (exec_dir / "latest_capital_proposals.json").write_text(json.dumps({
                "reserve":200,"deployable":800,
                "allocations":{"a":{"proposed":100},"b":{"proposed":50}}
            }))
            (exec_dir / "executive_dashboard.json").write_text(json.dumps({
                "safety":{"financial_execution":"proposal_only"}
            }))

            finance = ConsoleAggregator(home).snapshot()["finance"]
            self.assertEqual(finance["proposed_total"], 150.0)
            self.assertEqual(finance["execution_mode"], "proposal_only")

if __name__ == "__main__":
    unittest.main()
