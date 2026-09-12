import unittest
from companyos.runtime.self_evolution_engine import path_allowed
class T(unittest.TestCase):
 def test_business_logic_allowed(self):self.assertTrue(path_allowed("companyos/orchestration/example_improvement.py")[0])
 def test_wallet_blocked(self):self.assertFalse(path_allowed("companyos/walletintegration/signer.py")[0])
 def test_finance_blocked(self):self.assertFalse(path_allowed("companyos/finance_engine.py")[0])
 def test_connector_blocked(self):self.assertFalse(path_allowed("companyos/connectors_live/registry.py")[0])
 def test_supervisor_blocked(self):self.assertFalse(path_allowed("companyos/runtime/service_supervisor.py")[0])
 def test_self_guard_blocked(self):self.assertFalse(path_allowed("companyos/runtime/self_evolution_engine.py")[0])
 def test_config_blocked(self):self.assertFalse(path_allowed("config/connectors.json")[0])
 def test_traversal_blocked(self):self.assertFalse(path_allowed("../outside.py")[0])
if __name__=="__main__":unittest.main()
