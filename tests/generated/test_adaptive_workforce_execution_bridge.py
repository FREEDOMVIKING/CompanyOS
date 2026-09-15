from companyos.runtime.adaptive_workforce_execution_bridge import ROLE_ACTIONS,WorkforceExecutionBridge
def test_roles(): assert {"execution_readiness","revenue_evidence","market_validation","pricing","research"}<=set(ROLE_ACTIONS)
def test_safe_context_excludes_secrets():
 x=WorkforceExecutionBridge().safe_context({"title":"x","secret":"bad","private_key":"bad"})
 assert x=={"title":"x"}
def test_actions_are_bounded():
 s=" ".join(ROLE_ACTIONS.values()).lower()
 assert "transfer" not in s and "buy " not in s and "send money" not in s
