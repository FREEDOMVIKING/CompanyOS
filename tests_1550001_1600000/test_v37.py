import tempfile, unittest
from pathlib import Path
from companyos.autonomous_launch_control_v37.engine import AutonomousLaunchControlV37
from companyos.autonomous_launch_control_v37.storage import atomic_write_json

class V37Tests(unittest.TestCase):
    def make_home(self):
        td = tempfile.TemporaryDirectory()
        home = Path(td.name)
        live = home / ".companyos_runtime"
        live.mkdir()

        atomic_write_json(live / "autonomous_launch_director_v36_live.json", {
            "status":"autonomous_launch_director_ready",
            "launch_review_queue":[
                {
                    "review_id":"launch-v1",
                    "venture_id":"v1",
                    "venture_name":"Digital Template Business",
                    "launch_score":95,
                    "launch_state":"NEAR_READY",
                    "status":"EXECUTIVE_REVIEW_REQUIRED"
                },
                {
                    "review_id":"launch-v2",
                    "venture_id":"v2",
                    "venture_name":"AI Proposal Generator",
                    "launch_score":82,
                    "launch_state":"NEAR_READY",
                    "status":"EXECUTIVE_REVIEW_REQUIRED"
                }
            ],
            "ventures":[
                {"venture_id":"v1","name":"Digital Template Business","launch_score":95,"blockers":["validation_ready"]},
                {"venture_id":"v2","name":"AI Proposal Generator","launch_score":82,"blockers":["product_ready"]}
            ]
        })
        return td, home

    def test_initial_cycle(self):
        td, home = self.make_home()
        try:
            e = AutonomousLaunchControlV37(home)
            s = e.run_cycle()
            self.assertEqual(s["status"], "autonomous_launch_control_ready")
            self.assertEqual(s["analytics"]["pending"], 2)
            self.assertFalse(s["automatic_external_launch_enabled"])
        finally:
            td.cleanup()

    def test_approve(self):
        td, home = self.make_home()
        try:
            e = AutonomousLaunchControlV37(home)
            d = e.make_decision("launch-v1", "APPROVE", "Proceed with internal launch prep")
            self.assertEqual(d["new_status"], "APPROVED_FOR_LAUNCH_PREP")
            s = e.run_cycle()
            self.assertEqual(s["analytics"]["approved"], 1)
            self.assertEqual(len(s["approved_for_launch_prep"]), 1)
            self.assertFalse(s["approved_for_launch_prep"][0]["external_execution_enabled"])
        finally:
            td.cleanup()

    def test_hold_and_reject(self):
        td, home = self.make_home()
        try:
            e = AutonomousLaunchControlV37(home)
            e.make_decision("launch-v1", "HOLD")
            e.make_decision("launch-v2", "REJECT")
            s = e.run_cycle()
            self.assertEqual(s["analytics"]["held"], 1)
            self.assertEqual(s["analytics"]["rejected"], 1)
        finally:
            td.cleanup()

if __name__ == "__main__":
    unittest.main()
