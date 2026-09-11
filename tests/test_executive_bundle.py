import tempfile
import unittest
from pathlib import Path

from companyos.executive.capital import allocate_capital
from companyos.executive.dependencies import analyze_dependencies
from companyos.executive.engine import ExecutiveEngine
from companyos.executive.models import Venture, Worker
from companyos.executive.prioritizer import rank_ventures
from companyos.executive.scaling import recommend_scale_action
from companyos.executive.workforce import assign_workers


class ExecutiveBundleTests(unittest.TestCase):
    def ventures(self):
        return [
            Venture(
                venture_id="a",
                name="Alpha",
                stage="operations",
                expected_return=2.0,
                confidence=0.9,
                risk=0.2,
                urgency=0.8,
                strategic_fit=0.9,
                capital_requested=10000,
                workers_requested=1,
                progress=0.8,
                failure_probability=0.1,
                metrics={"demand": 0.9, "margin": 0.8, "retention": 0.8},
            ),
            Venture(
                venture_id="b",
                name="Beta",
                stage="validation",
                expected_return=0.4,
                confidence=0.4,
                risk=0.7,
                urgency=0.3,
                strategic_fit=0.4,
                capital_requested=5000,
                workers_requested=1,
                progress=0.2,
                failure_probability=0.5,
            ),
        ]

    def workers(self):
        return [
            Worker("w1", "growth", reliability=0.95),
            Worker("w2", "engineering", reliability=0.85),
        ]

    def test_priority_order(self):
        ranked = rank_ventures(self.ventures())
        self.assertEqual(ranked[0]["venture_id"], "a")

    def test_capital_reserve_and_limit(self):
        report = allocate_capital(self.ventures(), 20000)
        self.assertEqual(report["reserve"], 4000.0)
        self.assertLessEqual(report["allocations"]["a"]["proposed"], 15000.0)
        self.assertEqual(report["allocations"]["a"]["execution_status"], "proposal_only")

    def test_worker_assignment(self):
        assignments = assign_workers(self.ventures(), self.workers())
        assigned = assignments["a"] + assignments["b"]
        self.assertEqual(len(set(assigned)), len(assigned))

    def test_scaling(self):
        self.assertEqual(recommend_scale_action(self.ventures()[0]), "scale_up")

    def test_dependency_cycle(self):
        ventures = self.ventures()
        ventures[0].dependencies = ["b"]
        ventures[1].dependencies = ["a"]
        report = analyze_dependencies(ventures)
        self.assertTrue(report["cycles"])

    def test_full_cycle_writes_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = ExecutiveEngine(Path(tmp))
            result = engine.run_cycle(self.ventures(), self.workers(), 20000)
            self.assertTrue(result["audit"]["passed"])
            self.assertTrue((Path(tmp) / "executive_dashboard.json").exists())
            self.assertEqual(result["safety"]["financial_execution"], "proposal_only")


if __name__ == "__main__":
    unittest.main()
