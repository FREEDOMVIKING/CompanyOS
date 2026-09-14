import unittest
from companyos.runtime import capability_request_executor as r

class CapabilityRequestExecutorTests(unittest.TestCase):
    def good(self):
        return {
            "status":"research_required",
            "requested_capability":"x",
            "execution_allowed":False,
            "external_action_allowed":False,
            "financial_action_allowed":False,
            "credential_access_allowed":False,
            "deployment_allowed":False,
            "generation_contract":{
                "must_be_new_capability":True,
                "must_have_tests":True,
                "must_pass_isolated_validation":True,
                "must_not_duplicate_source":True,
                "promotion_requires_existing_expansion_pipeline":True,
            },
        }

    def test_accepts_guarded_request(self):
        ok,reason=r._eligible(self.good())
        self.assertTrue(ok,reason)

    def test_rejects_external_permission(self):
        q=self.good();q["external_action_allowed"]=True
        ok,_=r._eligible(q)
        self.assertFalse(ok)

if __name__=="__main__":
    unittest.main()
