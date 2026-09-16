import tempfile,unittest
from pathlib import Path
import companyos.runtime.durable_execution_closure as d
class T(unittest.TestCase):
 def test_contract(self):
  self.assertIn("COMPLETED",d.TERMINAL);self.assertNotIn("DISPATCHED",d.TERMINAL)
 def test_register(self):
  old=d.JOBS
  with tempfile.TemporaryDirectory() as td:
   d.JOBS=Path(td);a=d.register(oid="o1",packet_id="p1",candidate_name="c",candidate_score=5,selected_action={"action":"x"},fingerprint="f")
   b=d.register(oid="o1",packet_id="p2",candidate_name="changed",candidate_score=9,selected_action={"action":"y"},fingerprint="z")
   self.assertEqual(a["state"],"DISPATCHED");self.assertEqual(b["action_packet_id"],"p1")
  d.JOBS=old
if __name__=="__main__":unittest.main()
