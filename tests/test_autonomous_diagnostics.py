import unittest
from companyos.runtime import autonomous_diagnostics as d
class T(unittest.TestCase):
 def test_allowlist(self):
  self.assertEqual(d.plan({"findings":[{"kind":"credential","detail":"x"}]}),[])
  self.assertEqual(d.plan({"findings":[{"kind":"research_conversion_stall","detail":"x"}]})[0]["repair"],"request_targeted_enrichment")
if __name__=="__main__":unittest.main()
