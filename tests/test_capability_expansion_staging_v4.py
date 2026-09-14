import unittest
from companyos.runtime import capability_expansion as c

class ExpansionStagingImportTests(unittest.TestCase):
    def test_staged_package_imports(self):
        gap={"id":"candidate_gap_ranker","title":"x","reason":"x"}
        module = "CAPABILITY_ID='candidate_gap_ranker'\ndef capability_manifest():\n    return {'id': CAPABILITY_ID}\ndef evaluate(context):\n    return {'ok': True}\n"
        test = "import unittest\nfrom companyos.extensions.generated.candidate_gap_ranker import capability_manifest, evaluate\nclass T(unittest.TestCase):\n    def test_it(self):\n        self.assertEqual(capability_manifest()['id'], 'candidate_gap_ranker')\n        self.assertTrue(evaluate({})['ok'])\nif __name__ == '__main__':\n    unittest.main()\n"
        plan={"changes":[
            {"path":"wrong/module.py","content":module},
            {"path":"wrong/test.py","content":test},
        ]}
        cid,root,errors=c.stage_plan(gap,plan)
        self.assertEqual(errors,[])
        ok,steps=c.test_stage(root,gap["id"])
        self.assertTrue(ok,steps)

if __name__=="__main__":
    unittest.main()
