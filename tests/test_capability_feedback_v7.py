import unittest
from pathlib import Path
from companyos.runtime import capability_feedback as f

class CapabilityFeedbackTests(unittest.TestCase):
    def test_fingerprint_stable(self):
        p=Path.home()/'.companyos_runtime_feedback_test.py'
        p.write_text('x=1\n')
        self.assertEqual(f.source_fingerprint(p),f.source_fingerprint(p))
        p.unlink(missing_ok=True)

if __name__=='__main__':
    unittest.main()
