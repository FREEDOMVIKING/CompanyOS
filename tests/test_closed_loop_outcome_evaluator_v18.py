import unittest
from companyos.runtime import closed_loop_outcome_evaluator as o

class ClosedLoopOutcomeEvaluatorV18Tests(unittest.TestCase):
    def test_positive_outcome_scores_positive(self):
        before={"profit":10,"probability":40,"readiness":30,"score":50,"evidence_count":1}
        after={"profit":20,"probability":60,"readiness":55,"score":65,"evidence_count":3}
        u=o._score_outcome(before,after,{"success":True})
        self.assertGreater(u,0)

    def test_failed_outcome_penalized(self):
        before={"profit":10,"probability":50,"readiness":50,"score":50,"evidence_count":2}
        after=dict(before)
        u=o._score_outcome(before,after,{"failed":True})
        self.assertLess(u,0)

if __name__=="__main__":
    unittest.main()
