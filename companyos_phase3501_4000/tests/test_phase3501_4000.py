from companyos.venture_factory import OpportunityEngine,PortfolioEngine,VentureGuardrails
def test_rank():
 assert OpportunityEngine().rank([{"demand":1,"pain":1,"willingness_to_pay":1,"competition":0,"evidence":1}])[0]["opportunity_score"]>.9
def test_portfolio():
 assert PortfolioEngine().decide([{"venture_id":"x","score":.8,"growth":.3,"reliability":.8}])[0]["decision"]=="SCALE"
def test_guardrail():
 assert VentureGuardrails().route([{"kind":"contract_signature"}])["approval_queue"]
