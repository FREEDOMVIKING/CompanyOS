import tempfile, unittest
from pathlib import Path
from companyos.venture_promotion_pipeline_v39.engine import VenturePromotionPipelineV39
from companyos.venture_promotion_pipeline_v39.storage import atomic_write_json, read_json

class V39Tests(unittest.TestCase):
    def test_valid_promotion(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            live=home/".companyos_runtime"
            live.mkdir()
            atomic_write_json(live/"autonomous_launch_control_v37_live.json",{
                "approved_for_launch_prep":[{
                    "venture_id":"v1",
                    "venture_name":"Digital Template Business",
                    "review_id":"launch-v1",
                    "launch_score":95,
                    "status":"APPROVED_FOR_LAUNCH_PREP",
                    "external_execution_enabled":False
                }]
            })
            s=VenturePromotionPipelineV39(home).run_cycle()
            self.assertEqual(s["promoted"],1)
            out=read_json(live/"approved_for_launch_prep_v37.json",{})
            self.assertEqual(len(out["ventures"]),1)
            self.assertFalse(out["ventures"][0]["external_execution_enabled"])

    def test_reject_bad_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            live=home/".companyos_runtime"
            live.mkdir()
            atomic_write_json(live/"autonomous_launch_control_v37_live.json",{
                "approved_for_launch_prep":[{
                    "venture_id":"v1",
                    "venture_name":"Bad",
                    "review_id":"launch-v1",
                    "launch_score":80,
                    "status":"APPROVED_FOR_LAUNCH_PREP",
                    "external_execution_enabled":True
                }]
            })
            s=VenturePromotionPipelineV39(home).run_cycle()
            self.assertEqual(s["promoted"],0)
            self.assertEqual(s["failed"],1)

if __name__=="__main__":
    unittest.main()
