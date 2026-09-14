import unittest
from companyos.runtime import recursive_qualification as q

class RecursiveQualificationV15Tests(unittest.TestCase):
    def test_service_failure_detection(self):
        before={"a":{"running":True,"process_alive":True,"consecutive_failures":0}}
        after={"a":{"running":False,"process_alive":False,"consecutive_failures":1}}
        issues=q.bad_services(before,after)
        self.assertTrue(issues)

    def test_queue_snapshot_shape(self):
        snap=q.queue_snapshot()
        for key in ("total","research_required","generating","completed","rejected","latest"):
            self.assertIn(key,snap)

if __name__=="__main__":
    unittest.main()
