import tempfile, unittest
from pathlib import Path
from companyos.orchestrator.graph import build_graph
from companyos.orchestrator.workflows import create_workflows, trigger_ready_steps, detect_deadlocks
from companyos.orchestrator.delegation import build_delegations
from companyos.orchestrator.trends import trend_summary
from companyos.orchestrator.engine import OrchestratorEngine

class Tests(unittest.TestCase):
    def test_graph(self):
        g=build_graph([{"venture_id":"v1","name":"One"}],[],{},[],[])
        self.assertEqual(g["node_count"],1)

    def test_workflow_trigger(self):
        w=create_workflows([{"venture_id":"v1","milestone_id":"m1","milestone":"Do","week":1}],[])
        t=trigger_ready_steps(w)
        self.assertEqual(len(t),1)

    def test_deadlock(self):
        w=[{"workflow_id":"w","steps":[{"step_id":"s","depends_on":["missing"],"status":"waiting"}]}]
        self.assertEqual(len(detect_deadlocks(w)),1)

    def test_delegation(self):
        d=build_delegations([{"task_id":"t","venture_id":"v","assigned_agent":"a","desired_pool":"engineering"}],
                            {"a":{"pool":"engineering","reliability":1}})
        self.assertEqual(d[0]["status"],"delegated")

    def test_trend(self):
        self.assertEqual(trend_summary([{"average_venture_health":0.1,"task_assignment_rate":0.2},
                                        {"average_venture_health":0.5,"task_assignment_rate":0.8}])["venture_health_trend"],"up")

    def test_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            (home/"companyos_runtime"/"opscenter").mkdir(parents=True)
            r=OrchestratorEngine(home).run_cycle()
            self.assertEqual(r["phase"],"18701-19000")
            self.assertTrue((home/"companyos_runtime"/"orchestrator"/"latest_orchestration.json").exists())

if __name__=="__main__":
    unittest.main()
