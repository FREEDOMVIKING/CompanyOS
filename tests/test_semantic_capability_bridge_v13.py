import unittest
from companyos.runtime import semantic_capability_bridge as b

class SemanticCapabilityBridgeV13Tests(unittest.TestCase):
    def test_maps_missing_executable_next_action(self):
        self.assertEqual(
            b.requested_capability_for("missing_executable_next_action"),
            "executable_next_action_planner",
        )

    def test_extracts_top_bottleneck(self):
        result={"top_bottleneck":{"reason":"missing_executable_next_action","severity":21.0,"unresolved":True}}
        signals=b._signals_from_result(result)
        self.assertEqual(len(signals),1)
        self.assertEqual(signals[0]["reason"],"missing_executable_next_action")

    def test_request_stays_internal(self):
        req=b._request(
            {"requested_capability":"candidate_gap_ranker_downstream_gap_detector"},
            {"reason":"missing_executable_next_action","severity":21.0,"source":"top_bottleneck","detail":{}},
        )
        self.assertFalse(req["execution_allowed"])
        self.assertFalse(req["external_action_allowed"])
        self.assertFalse(req["financial_action_allowed"])
        self.assertFalse(req["credential_access_allowed"])
        self.assertFalse(req["deployment_allowed"])
        self.assertEqual(req["status"],"research_required")

if __name__=="__main__":
    unittest.main()
