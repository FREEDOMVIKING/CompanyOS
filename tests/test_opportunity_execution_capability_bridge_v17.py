import unittest
from companyos.runtime import opportunity_execution_capability_bridge as b

class OpportunityExecutionCapabilityBridgeV17Tests(unittest.TestCase):
    def test_bottleneck_becomes_action(self):
        c={"name":"x","source":"x","score":70,"payload":{"customer":"buyer","price":10,"evidence":["a"]}}
        results=[{"capability_id":"gap","ok":True,"result":{"top_bottleneck":{"reason":"missing_executable_next_action","severity":21,"unresolved":True}}}]
        actions=b.extract_actions(c,results)
        self.assertTrue(actions)
        self.assertIn("measurable",actions[0]["action"].lower())

    def test_packet_preserves_existing_policy_gates(self):
        c={"name":"x","source":"x","score":70,"payload":{}}
        p=b.build_packet(c,[],[{"source":"x","action":"validate","confidence":70}])
        self.assertEqual(p["financial_action_allowed"],"existing_policy_only")
        self.assertEqual(p["external_action_allowed"],"existing_policy_only")

if __name__=="__main__":
    unittest.main()
