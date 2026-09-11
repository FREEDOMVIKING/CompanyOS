import json
import tempfile
import unittest
from pathlib import Path

from companyos.opscenter.agents import build_agent_registry, route_tasks
from companyos.opscenter.planning import build_roadmap, forecast_bottlenecks
from companyos.opscenter.analytics import venture_health, calculate_kpis
from companyos.opscenter.aggregator import OperationsAggregator
from companyos.opscenter.engine import OperationsEngine

class OpsCenterTests(unittest.TestCase):
    def test_agent_registry_and_routing(self):
        workers = [{"worker_id":"w1","specialty":"engineering","capacity":1,"current_load":0,"reliability":0.9}]
        registry = build_agent_registry(workers)
        tasks = [{"task_id":"t1","venture_id":"v1","action":"build_product","priority_score":1}]
        routed = route_tasks(tasks, registry)
        self.assertEqual(routed[0]["assigned_agent"], "w1")
        self.assertEqual(routed[0]["desired_pool"], "engineering")

    def test_roadmap_generation(self):
        roadmap = build_roadmap([{"venture_id":"v1","name":"One","stage":"build","progress":0.4,"priority_score":1}])
        self.assertEqual(len(roadmap), 3)
        self.assertTrue(all(x["venture_id"] == "v1" for x in roadmap))

    def test_bottleneck_forecast(self):
        ventures = [{"venture_id":"v1","name":"One","blocked":True,"failure_probability":0.6,"dependencies":[]}]
        alerts = forecast_bottlenecks(ventures, [], [])
        self.assertTrue(alerts)
        self.assertGreaterEqual(alerts[0]["severity"], 0.7)

    def test_health_score_bounds(self):
        self.assertGreaterEqual(venture_health({"progress":1,"confidence":1,"risk":0,"failure_probability":0}), 0.9)
        self.assertEqual(venture_health({"progress":0,"confidence":0,"risk":1,"failure_probability":1,"blocked":True}), 0.0)

    def test_full_snapshot_and_kpis(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            exec_dir = home / "companyos_runtime" / "phase18201_18300"
            control_dir = home / "companyos_runtime" / "controlplane"
            exec_dir.mkdir(parents=True)
            control_dir.mkdir(parents=True)

            (exec_dir / "ventures.json").write_text(json.dumps([{
                "venture_id":"v1","name":"One","stage":"validation","progress":0.3,
                "confidence":0.7,"risk":0.3,"failure_probability":0.2,"dependencies":[]
            }]))
            (exec_dir / "workers.json").write_text(json.dumps([{
                "worker_id":"w1","specialty":"research","capacity":1,"current_load":0,"reliability":0.9
            }]))
            (exec_dir / "latest_priority_ranking.json").write_text(json.dumps([{"venture_id":"v1","score":1.1}]))
            (exec_dir / "latest_executive_decisions.json").write_text(json.dumps([{
                "venture_id":"v1","scale_action":"validate_next","priority_score":1.1,
                "capital_proposed":100,"approval_required":True
            }]))

            snapshot = OperationsAggregator(home).snapshot()
            self.assertEqual(snapshot["phase"], "18501-18700")
            self.assertEqual(snapshot["kpis"]["venture_count"], 1)
            self.assertEqual(snapshot["routed_tasks"][0]["assigned_agent"], "w1")

    def test_engine_persists_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "companyos_runtime" / "phase18201_18300").mkdir(parents=True)
            (home / "companyos_runtime" / "controlplane").mkdir(parents=True)
            result = OperationsEngine(home).run_cycle()
            self.assertEqual(result["phase"], "18501-18700")
            self.assertTrue((home / "companyos_runtime" / "opscenter" / "latest_ops_snapshot.json").exists())

if __name__ == "__main__":
    unittest.main()
