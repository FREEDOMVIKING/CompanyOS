import json,tempfile,unittest
from pathlib import Path
from companyos.stability_tools.worker import atomic_json
from companyos.stability_tools.status_cli import failed_services

class Tests(unittest.TestCase):
    def test_atomic_json(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"x.json";atomic_json(p,{"ok":True})
            self.assertTrue(json.loads(p.read_text())["ok"])
    def test_failed(self):
        d={"services":{"a":{"enabled":True,"alive":False},"b":{"enabled":True,"alive":True},"c":{"enabled":False,"alive":False}}}
        self.assertEqual(failed_services(d),["a"])
    def test_runtime_imports(self):
        import companyos.customer_acquisition_v2.runtime
        import companyos.memory_graph.runtime
        import companyos.profitability_optimizer.runtime
        import companyos.resource_allocator.runtime
        import companyos.risk_compliance.runtime
        import companyos.strategic_planner.runtime

if __name__=="__main__":unittest.main()
