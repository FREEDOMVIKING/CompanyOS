import unittest
from companyos.runtime import recursive_improvement_controller as r

class RecursiveImprovementV12Tests(unittest.TestCase):
    def test_lineage_guard(self):
        req={"requested_capability":"a","source_capability":"a"}
        ok,reason=r.request_guard(req,{"seen_requests":{}},0)
        self.assertFalse(ok)
        self.assertEqual(reason,"self_cycle")

    def test_regression_detection(self):
        before={"service_failures":0,"quarantined":0,"failures":0,"active":2}
        after={"service_failures":1,"quarantined":0,"failures":0,"active":2}
        reasons=r.detect_regression(before,after,None)
        self.assertIn("service_failures_increased",reasons)

    def test_limits(self):
        now=10000
        h={"promotions":[{"ts":9999},{"ts":9998},{"ts":9997}],"seen_requests":{},"cycles":0}
        ok,reason=r.promotion_limits_ok(h,now)
        self.assertFalse(ok)
        self.assertEqual(reason,"hourly_promotion_limit")

if __name__=="__main__":
    unittest.main()
