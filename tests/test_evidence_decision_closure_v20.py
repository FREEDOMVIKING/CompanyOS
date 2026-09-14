import unittest
from companyos.runtime import evidence_decision_closure as d

class EvidenceDecisionClosureV20Tests(unittest.TestCase):
    def test_promotes_only_with_evidence_and_economics(self):
        metrics={"profit":10,"probability":60,"readiness":30,"score":70}
        evidence={"total":4,"observed":4,"coverage":1.0,"missing_critical":[]}
        recalc=d.recompute_readiness(metrics,evidence)
        decision,_=d.decide(metrics,evidence,recalc)
        self.assertEqual(decision,"promote_to_guarded_execution")

    def test_missing_profit_deprioritizes(self):
        metrics={"profit":0,"probability":60,"readiness":60,"score":70}
        evidence={"total":4,"observed":4,"coverage":1.0,"missing_critical":[]}
        decision,_=d.decide(metrics,evidence,80)
        self.assertEqual(decision,"deprioritize")

    def test_missing_critical_evidence_blocks(self):
        metrics={"profit":10,"probability":60,"readiness":60,"score":70}
        evidence={"total":4,"observed":3,"coverage":0.75,"missing_critical":["pricing"]}
        decision,_=d.decide(metrics,evidence,80)
        self.assertEqual(decision,"continue_research")

if __name__=="__main__":
    unittest.main()
