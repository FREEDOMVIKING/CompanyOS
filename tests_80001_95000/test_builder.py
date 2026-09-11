import tempfile,unittest
from pathlib import Path
from companyos.venture_builder_v3.engine import VentureBuilder,write_json
class TestBuilder(unittest.TestCase):
    def test_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td)
            write_json(h/'companyos_runtime'/'roadmap_execution_70001_80000'/'active_execution.json',{'execution':{'execution_id':'exec-test','subject':'digital template business','state':'PLANNING'}})
            r=VentureBuilder(h).run()
            self.assertEqual(r['status'],'ready_for_review')
            self.assertTrue(Path(r['builder']['workspace']).exists())
            self.assertEqual(r['builder']['deployment_queue_length'],1)
if __name__=='__main__': unittest.main()
