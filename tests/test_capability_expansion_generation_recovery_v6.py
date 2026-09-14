import unittest
from companyos.runtime import capability_expansion as c

class CapabilityGenerationRecoveryV6Tests(unittest.TestCase):
    def test_recovers_complete_object_from_wrapped_text(self):
        x=c._recover_json_object('noise {"title":"x","reason":"y","changes":[],"tests":[],"integration":"z"} tail')
        self.assertIsInstance(x,dict)
        self.assertEqual(x["title"],"x")

    def test_rejects_incomplete_json(self):
        self.assertIsNone(c._recover_json_object('{"title":"x","changes":['))

    def test_minimal_prompt_contains_exact_paths(self):
        m,t=c.canonical_paths("candidate_gap_ranker")
        p=c._minimal_generation_prompt({"id":"candidate_gap_ranker","reason":"x"},m,t,2)
        self.assertIn(m,p)
        self.assertIn(t,p)
        self.assertIn("Return ONE complete JSON object only",p)

if __name__=="__main__":
    unittest.main()
