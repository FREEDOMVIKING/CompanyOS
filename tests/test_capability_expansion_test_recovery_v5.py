import unittest
from companyos.runtime import capability_expansion as c

class CapabilityExpansionTestRecoveryV5(unittest.TestCase):
    def test_recovers_top_level_test_source(self):
        plan={
            "changes":[{"path":"companyos/extensions/generated/x.py","content":"CAPABILITY_ID='x'\ndef capability_manifest(): return {'id':'x'}\ndef evaluate(context): return {'ok':True}\n"}],
            "tests":{"path":"tests/generated/test_x.py","content":"import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n"}
        }
        m,t,e=c._classify_generated_contents(plan,"x")
        self.assertIsNotNone(m)
        self.assertIn("import unittest",t)
        self.assertNotIn("test_content_missing",e)

    def test_builds_contract_test_when_model_omits_one(self):
        plan={"changes":[{"path":"companyos/extensions/generated/x.py","content":"CAPABILITY_ID='x'\ndef capability_manifest(): return {'id':'x'}\ndef evaluate(context): return {'ok':True}\n"}],"tests":[]}
        m,t,e=c._classify_generated_contents(plan,"x")
        self.assertIsNotNone(m)
        self.assertIn("GeneratedCapabilityContractTests",t)
        self.assertEqual(e,[])

    def test_staged_contract_executes(self):
        gap={"id":"x","title":"x","reason":"x"}
        plan={"changes":[{"path":"whatever.py","content":"CAPABILITY_ID='x'\ndef capability_manifest(): return {'id':'x'}\ndef evaluate(context): return {'ok':True}\n"}],"tests":[]}
        cid,root,errors=c.stage_plan(gap,plan)
        self.assertEqual(errors,[])
        ok,steps=c.test_stage(root,"x")
        self.assertTrue(ok,steps)

if __name__=="__main__":
    unittest.main()
