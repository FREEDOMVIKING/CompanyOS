import unittest
from companyos.runtime import autonomous_evidence_acquisition as e

class AutonomousEvidenceAcquisitionV19Tests(unittest.TestCase):
    def test_missing_external_evidence_expands_requirements(self):
        packet={
            "candidate_name":"x",
            "capability_results":[
                {"ok":True,"capability_id":"gap","result":{"top_bottleneck":{"reason":"missing_external_evidence","unresolved":True}}}
            ]
        }
        reqs=e.requirements_from_packet(packet)
        kinds={r["requirement"] for r in reqs}
        self.assertIn("provenance",kinds)
        self.assertIn("corroboration",kinds)
        self.assertIn("traceability",kinds)

    def test_tasks_are_research_only(self):
        packet={"candidate_name":"x","action_packet_id":"a"}
        tasks=e.build_tasks(packet,[{"requirement":"pricing","guidance":"g","source":"s"}])
        self.assertFalse(tasks[0]["external_send_allowed"])
        self.assertFalse(tasks[0]["financial_action_allowed"])
        self.assertFalse(tasks[0]["credential_access_allowed"])
        self.assertFalse(tasks[0]["deployment_allowed"])

if __name__=="__main__":
    unittest.main()
