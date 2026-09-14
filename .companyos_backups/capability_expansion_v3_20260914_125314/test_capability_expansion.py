import unittest
from companyos.runtime import capability_expansion as c
class T(unittest.TestCase):
 def test_blocks_network_and_secrets(self):
  self.assertTrue(c.validate("companyos/extensions/generated/x.py","import urllib\nOPENAI_API_KEY='x'","x"))
 def test_accepts_pure_module(self):
  src='CAPABILITY_ID="x"\ndef capability_manifest(): return {"id":"x"}\ndef evaluate(context): return {"ok":True}\n'
  self.assertEqual(c.validate("companyos/extensions/generated/x.py",src,"x"),[])
 def test_gap(self):
  g=c.derive_gap({"findings":[{"kind":"research_conversion_stall"}],"profit":{},"bridge":{},"services":{}})
  self.assertEqual(g["id"],"research_quality_analyzer")
if __name__=="__main__":unittest.main()
