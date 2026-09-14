import unittest
from companyos.runtime import profit_directed_capability_priority as p

class ProfitDirectedCapabilityPriorityV16Tests(unittest.TestCase):
    def test_execution_gap_scores_above_meta_gap(self):
        signals={"missing_executable_next_action":40}
        a={"requested_capability":"executable_next_action_planner","reason":"missing_executable_next_action","priority":70}
        b={"requested_capability":"candidate_gap_ranker_downstream_gap_detector","reason":"generic recursion","priority":70}
        self.assertGreater(p.score_request(a,signals),p.score_request(b,signals))

    def test_score_is_bounded(self):
        req={"requested_capability":"profit_revenue_margin_sales_pricing","priority":500}
        self.assertLessEqual(p.score_request(req,{}),200)

if __name__=="__main__":
    unittest.main()
