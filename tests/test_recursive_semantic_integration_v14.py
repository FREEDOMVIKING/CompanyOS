import unittest
from pathlib import Path

class RecursiveSemanticIntegrationV14Tests(unittest.TestCase):
    def test_controller_contains_semantic_bridge_both_sides(self):
        s=Path("companyos/runtime/recursive_improvement_controller.py").read_text(encoding="utf-8")
        self.assertIn("semantic_before=semantic.cycle()",s)
        self.assertIn("semantic_after=semantic.cycle()",s)
        self.assertIn("from companyos.runtime import semantic_capability_bridge as semantic",s)

    def test_one_executor_call_per_controller_cycle_source(self):
        s=Path("companyos/runtime/recursive_improvement_controller.py").read_text(encoding="utf-8")
        self.assertEqual(s.count("executor.cycle()"),1)

if __name__=="__main__":
    unittest.main()
