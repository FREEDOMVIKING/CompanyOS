import tempfile, unittest
from pathlib import Path
from companyos.autonomous_execution_engine_v38.engine import AutonomousExecutionEngineV38
from companyos.autonomous_execution_engine_v38.storage import atomic_write_json

class V38Tests(unittest.TestCase):
    def make_home(self):
        td = tempfile.TemporaryDirectory()
        home = Path(td.name)
        live = home / ".companyos_runtime"
        live.mkdir()
        atomic_write_json(live / "approved_for_launch_prep_v37.json", {
            "ventures":[
                {
                    "venture_id":"v1",
                    "venture_name":"Digital Template Business",
                    "review_id":"launch-v1",
                    "launch_score":95,
                    "status":"APPROVED_FOR_LAUNCH_PREP",
                    "external_execution_enabled":False
                }
            ]
        })
        return td, home

    def test_prepare_execution(self):
        td, home = self.make_home()
        try:
            e = AutonomousExecutionEngineV38(home)
            s = e.run_cycle()
            self.assertEqual(s["status"], "autonomous_execution_engine_ready")
            self.assertEqual(s["approved_ventures_received"], 1)
            self.assertEqual(s["ready_for_external_execution_review"], 1)
            self.assertFalse(s["automatic_external_execution_enabled"])
            x = s["executions"][0]
            self.assertTrue(Path(x["artifacts"]["website_index"]).exists())
            self.assertTrue(Path(x["artifacts"]["checkout_manifest"]).exists())
        finally:
            td.cleanup()

    def test_empty_queue(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            (home/".companyos_runtime").mkdir()
            e = AutonomousExecutionEngineV38(home)
            s = e.run_cycle()
            self.assertEqual(s["executions_total"], 0)

if __name__ == "__main__":
    unittest.main()
