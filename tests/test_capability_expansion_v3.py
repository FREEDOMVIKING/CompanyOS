import unittest
from companyos.runtime import capability_expansion as c

class CapabilityExpansionV3Tests(unittest.TestCase):
    def test_canonical_paths(self):
        self.assertEqual(
            c.canonical_paths("Candidate Gap Ranker"),
            (
                "companyos/extensions/generated/candidate_gap_ranker.py",
                "tests/generated/test_candidate_gap_ranker.py",
            ),
        )

    def test_plan_path_normalization_ignores_model_paths(self):
        plan={"changes":[
            {"path":"wrong/module.py","content":"CAPABILITY_ID='x'\\ndef capability_manifest(): return {'id':'x'}\\ndef evaluate(context): return {'ok':True}\\n"},
            {"path":"also/wrong.py","content":"import unittest\\nclass T(unittest.TestCase):\\n def test_x(self): self.assertTrue(True)\\nif __name__=='__main__': unittest.main()\\n"},
        ]}
        m,t,e=c._classify_generated_contents(plan)
        self.assertIsNotNone(m); self.assertIsNotNone(t); self.assertEqual(e,[])

    def test_blocks_network(self):
        e=c.validate_source("companyos/extensions/generated/x.py","import urllib\\nCAPABILITY_ID='x'\\ndef capability_manifest(): return {}\\ndef evaluate(context): return {}\\n","x",False)
        self.assertTrue(e)

if __name__=="__main__":
    unittest.main()
