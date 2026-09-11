
import tempfile, unittest
from pathlib import Path
from companyos.autonomous_customer_success_v33.engine import CustomerSuccessV33
class T(unittest.TestCase):
    def test_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            s=CustomerSuccessV33(Path(td)).run_cycle()
            self.assertEqual(s["status"],"autonomous_customer_success_ready")
            self.assertFalse(s["automatic_refunds_enabled"])
if __name__=="__main__": unittest.main()
